"""
Matchmaking Service — автоматический фоновый поиск соперников
Запускается в отдельном потоке при старте приложения.
Использует APScheduler для периодической проверки очереди.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from models import MatchmakingQueue, Match, PlayerRating, User, TournamentParticipation, get_db

logger = logging.getLogger(__name__)

# Настройки матчмейкинга
ELO_RANGE_DEFAULT = 200       # Стандартный диапазон ELO ±200
ELO_RANGE_EXPANDED = 400      # Расширенный диапазон через 2 мин
ELO_RANGE_WIDE = 600          # Широкий диапазон через 5 мин
MAX_WAIT_TIME = 600           # Макс. время ожидания (10 мин)
CHECK_INTERVAL = 5            # Проверка каждые 5 секунд
MIN_GAMES_FOR_RANKED = 5      # Мин. игр для рейтингового матчмейкинга


class MatchmakingService:
    """Фоновый сервис поиска матчей"""

    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """Запустить фоновый цикл матчмейкинга"""
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._matchmaking_loop())
        logger.info("Matchmaking service started")

    async def stop(self):
        """Остановить фоновый цикл"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Matchmaking service stopped")

    async def _matchmaking_loop(self):
        """Основной цикл матчмейкинга"""
        while self.running:
            try:
                db = next(get_db())
                await self._process_queues(db)
                db.close()
            except Exception as e:
                logger.error(f"Matchmaking loop error: {e}")
            await asyncio.sleep(CHECK_INTERVAL)

    async def _process_queues(self, db: Session):
        """Обработка всех очередей матчмейкинга"""
        # Получаем ожидающих игроков, отсортированных по времени ожидания
        queues = db.query(MatchmakingQueue).filter(
            MatchmakingQueue.status == "waiting"
        ).order_by(MatchmakingQueue.queued_at).all()

        if not queues:
            return

        now = datetime.utcnow()

        # Обрабатываем таймауты
        for q in queues:
            wait_time = (now - q.queued_at).total_seconds()
            if wait_time > MAX_WAIT_TIME:
                q.status = "timeout"
                logger.info(f"Queue timeout for user {q.user_id} after {wait_time:.0f}s")
                db.commit()

        # Получаем актуальный список ожидающих
        waiting = db.query(MatchmakingQueue).filter(
            MatchmakingQueue.status == "waiting"
        ).order_by(MatchmakingQueue.queued_at).all()

        # Группируем по дисциплине и типу игры
        grouped = {}
        for q in waiting:
            key = (q.discipline_id, q.game_type)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(q)

        # Для каждой группы пытаемся найти совпадения
        for (discipline_id, game_type), players in grouped.items():
            if len(players) < 2:
                continue

            team_size = self._get_team_size(game_type)
            if len(players) >= team_size * 2:
                # Достаточно игроков для создания матча
                self._create_match(db, players[:team_size * 2], discipline_id)

    def _get_team_size(self, game_type: str) -> int:
        """Определить размер команды по типу игры"""
        sizes = {"1v1": 1, "2v2": 2, "5v5": 5}
        return sizes.get(game_type, 1)

    def _get_elo_range(self, base_elo: int, wait_time: float) -> Tuple[int, int]:
        """Динамический диапазон ELO в зависимости от времени ожидания"""
        if wait_time < 120:
            delta = ELO_RANGE_DEFAULT
        elif wait_time < 300:
            delta = ELO_RANGE_EXPANDED
        else:
            delta = ELO_RANGE_WIDE

        return max(0, base_elo - delta), base_elo + delta

    def _create_match(self, db: Session, players: List[MatchmakingQueue], discipline_id: int):
        """Создать матч из очереди игроков"""
        now = datetime.utcnow()

        # Разделяем на две команды (по ELO)
        players.sort(key=lambda p: p.elo)
        mid = len(players) // 2
        team1_players = players[:mid]
        team2_players = players[mid:]

        # Проверяем совместимость ELO
        avg_elo_t1 = sum(p.elo for p in team1_players) / len(team1_players)
        avg_elo_t2 = sum(p.elo for p in team2_players) / len(team2_players)

        if abs(avg_elo_t1 - avg_elo_t2) > ELO_RANGE_WIDE:
            logger.warning(f"ELO mismatch too large: {avg_elo_t1:.0f} vs {avg_elo_t2:.0f}")
            return

        # Создаём турнирную запись для каждой команды
        team1_participation = self._create_participation(db, team1_players, "Team 1")
        team2_participation = self._create_participation(db, team2_players, "Team 2")

        # Создаём матч
        match = Match(
            tournament_id=None,  # Матчмейкинг матч, не турнирный
            team1_id=team1_participation.id,
            team2_id=team2_participation.id,
            round="Matchmaking",
            status="pending",
            scheduled_at=now,
        )
        db.add(match)
        db.flush()

        # Обновляем записи в очереди
        for p in players:
            p.status = "found"
            p.found_at = now
            p.match_id = match.id

        db.commit()

        logger.info(
            f"Match created: {len(team1_players)}v{len(team2_players)} "
            f"(ELO {avg_elo_t1:.0f} vs {avg_elo_t2:.0f})"
        )

        # TODO: Отправить уведомления игрокам
        # TODO: Запустить таймер подтверждения результата

    def _create_participation(self, db: Session, players: List[MatchmakingQueue], team_name: str):
        """Создать запись участия для команды матчмейкинга"""
        # Создаём «виртуальную» команду для матчмейкинга
        participation = TournamentParticipation(
            tournament_id=None,
            user_id=players[0].user_id,  # Капитан
            is_confirmed=True,
        )
        db.add(participation)
        db.flush()
        return participation


# Глобальный инстанс
matchmaking_service = MatchmakingService()


# ==================== API Endpoints для матчмейкинга ====================

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from auth import get_current_user_from_cookie
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/matchmaking", tags=["matchmaking"])


class QueueResponse(BaseModel):
    status: str
    position: int = 0
    elo: int = 0
    wait_time: int = 0
    estimated_time: Optional[int] = None


@router.post("/queue", response_model=QueueResponse)
async def join_queue(
    discipline: str = Query(..., description="Slug дисциплины"),
    game_type: str = Query("1v1", description="Тип: 1v1, 2v2, 5v5"),
    db: Session = Depends(get_db),
    request=None
):
    """Встать в очередь матчмейкинга"""
    from models import Discipline

    # Получаем текущего запрос из request
    if request:
        user = get_current_user_from_cookie(request, db)
    else:
        user = None

    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    # Проверяем существующую очередь
    existing = db.query(MatchmakingQueue).filter(
        MatchmakingQueue.user_id == user.id,
        MatchmakingQueue.status.in_(["waiting", "found"])
    ).first()

    if existing:
        wait_time = int((datetime.utcnow() - existing.queued_at).total_seconds())
        return QueueResponse(
            status="already_queued",
            elo=existing.elo,
            wait_time=wait_time
        )

    # Получаем или создаём рейтинг
    from utils import get_or_create_rating
    rating = get_or_create_rating(db, user.id, disc.id)

    # Проверяем минимальное количество игр
    if rating.games_played < MIN_GAMES_FOR_RANKED:
        raise HTTPException(
            status_code=400,
            detail=f"Необходимо минимум {MIN_GAMES_FOR_RANKED} игр для матчмейкинга"
        )

    # Создаём запись в очереди
    queue_entry = MatchmakingQueue(
        user_id=user.id,
        discipline_id=disc.id,
        game_type=game_type,
        elo=rating.elo,
        status="waiting",
        queued_at=datetime.utcnow(),
    )
    db.add(queue_entry)
    db.commit()

    return QueueResponse(
        status="queued",
        elo=rating.elo,
        wait_time=0,
        estimated_time=180  # ~3 минуты
    )


@router.get("/status")
async def get_queue_status(
    db: Session = Depends(get_db),
    request=None
):
    """Статус очереди пользователя"""
    if request:
        user = get_current_user_from_cookie(request, db)
    else:
        user = None

    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    queue = db.query(MatchmakingQueue).filter(
        MatchmakingQueue.user_id == user.id,
        MatchmakingQueue.status.in_(["waiting", "found"])
    ).order_by(MatchmakingQueue.queued_at.desc()).first()

    if not queue:
        return {"status": "not_in_queue"}

    wait_time = int((datetime.utcnow() - queue.queued_at).total_seconds())

    # Подсчёт позиции в очереди
    position = db.query(MatchmakingQueue).filter(
        MatchmakingQueue.status == "waiting",
        MatchmakingQueue.queued_at < queue.queued_at
    ).count()

    return {
        "status": queue.status,
        "game_type": queue.game_type,
        "elo": queue.elo,
        "wait_time": wait_time,
        "position": position + 1,
        "estimated_time": max(0, 180 - wait_time),
    }


@router.delete("/queue")
async def leave_queue(
    db: Session = Depends(get_db),
    request=None
):
    """Выйти из очереди матчмейкинга"""
    if request:
        user = get_current_user_from_cookie(request, db)
    else:
        user = None

    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    queue = db.query(MatchmakingQueue).filter(
        MatchmakingQueue.user_id == user.id,
        MatchmakingQueue.status == "waiting"
    ).first()

    if queue:
        queue.status = "cancelled"
        db.commit()
        return {"status": "cancelled", "message": "Вы вышли из очереди"}

    return {"status": "not_in_queue"}
