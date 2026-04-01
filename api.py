"""
API Endpoints для EasyCyberPro
REST API для frontend-разработки и мобильных приложений
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from models import get_db, User, News, Discipline, Team, Tournament, PlayerRating, RatingChange, MatchmakingQueue, Match, TournamentParticipation
from schemas import (
    NewsResponse, NewsListResponse,
    DisciplineResponse, DisciplineListResponse,
    TeamResponse, TeamListResponse,
    TournamentResponse, TournamentListResponse,
    UserResponse, HealthResponse,
    LeaderboardResponse, LeaderboardItem,
    RatingHistoryResponse, RatingChangeResponse,
    UserRatingsResponse, UserRatingSummary,
    MatchmakingQueueResponse, PlayerRatingResponse
)
from auth import get_current_user_from_cookie
from utils import (
    get_level_by_elo, calculate_elo_change, update_player_rating,
    get_or_create_rating, BASE_ELO
)

router = APIRouter(prefix="/api/v1", tags=["API"])


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_api(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить текущего пользователя"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    return user


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка статуса сервиса"""
    return {
        "status": "ok",
        "service": "EasyCyberPro",
        "version": "1.0.0"
    }


@router.get("/news", response_model=NewsListResponse)
async def get_news_list(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    published_only: bool = True,
    db: Session = Depends(get_db)
):
    """Получить список новостей с пагинацией"""
    offset = (page - 1) * limit

    query = db.query(News)
    if published_only:
        query = query.filter(News.is_published == True)

    total = query.count()
    news_list = query.order_by(News.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "items": news_list,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/news/{news_id}", response_model=NewsResponse)
async def get_news(news_id: int, db: Session = Depends(get_db)):
    """Получить новость по ID"""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="Новость не найдена")
    return news


@router.get("/disciplines", response_model=DisciplineListResponse)
async def get_disciplines(db: Session = Depends(get_db)):
    """Получить список всех дисциплин"""
    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
    return {"items": disciplines, "total": len(disciplines)}


@router.get("/disciplines/{slug}", response_model=DisciplineResponse)
async def get_discipline(slug: str, db: Session = Depends(get_db)):
    """Получить дисциплину по slug"""
    discipline = db.query(Discipline).filter(Discipline.slug == slug).first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    return discipline


@router.get("/teams", response_model=TeamListResponse)
async def get_teams(
    discipline: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Получить список команд с фильтрацией и пагинацией"""
    offset = (page - 1) * limit

    query = db.query(Team).filter(Team.is_active == True)

    if discipline:
        disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
        if disc:
            query = query.filter(Team.discipline_id == disc.id)

    total = query.count()
    teams = query.order_by(Team.rating.desc()).offset(offset).limit(limit).all()

    return {
        "items": teams,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(team_id: int, db: Session = Depends(get_db)):
    """Получить команду по ID"""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Команда не найдена")
    return team


@router.get("/tournaments", response_model=TournamentListResponse)
async def get_tournaments(
    status: Optional[str] = None,
    discipline: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Получить список турниров с фильтрами"""
    offset = (page - 1) * limit

    query = db.query(Tournament)

    if status:
        query = query.filter(Tournament.status == status)

    if discipline:
        disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
        if disc:
            query = query.filter(Tournament.discipline_id == disc.id)

    total = query.count()
    tournaments = query.order_by(Tournament.start_date.desc()).offset(offset).limit(limit).all()

    return {
        "items": tournaments,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/tournaments/{tournament_id}", response_model=TournamentResponse)
async def get_tournament(tournament_id: int, db: Session = Depends(get_db)):
    """Получить турнир по ID"""
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Турнир не найден")
    return tournament


# ==================== СИСТЕМА РЕЙТИНГА ELO ====================

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    discipline: str = Query(..., description="Slug дисциплины"),
    limit: int = Query(50, ge=1, le=100, description="Количество игроков"),
    db: Session = Depends(get_db)
):
    """
    Таблица лидеров по дисциплине.
    
    Возвращает топ игроков по ELO с их статистикой.
    """
    disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    
    # Получаем топ игроков с данными пользователей
    ratings = db.query(PlayerRating).options(
        joinedload(PlayerRating.user)
    ).filter(
        PlayerRating.discipline_id == disc.id
    ).order_by(PlayerRating.elo.desc()).limit(limit).all()
    
    # Формируем ответ
    items = []
    for rank, rating in enumerate(ratings, 1):
        items.append(LeaderboardItem(
            rank=rank,
            user_id=rating.user_id,
            username=rating.user.username,
            avatar_url=rating.user.avatar_url,
            elo=rating.elo,
            level=rating.level,
            games_played=rating.games_played,
            wins=rating.wins,
            losses=rating.losses,
            win_rate=rating.win_rate,
            peak_elo=rating.peak_elo
        ))
    
    return {
        "discipline": discipline,
        "discipline_name": disc.name,
        "items": items,
        "total": len(items),
        "limit": limit
    }


@router.get("/leaderboards", response_model=List[DisciplineResponse])
async def get_all_leaderboards(db: Session = Depends(get_db)):
    """Получить список всех дисциплин с таблицами лидеров"""
    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
    return disciplines


@router.get("/users/{user_id}/ratings", response_model=UserRatingsResponse)
async def get_user_ratings(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Получить все рейтинги пользователя по дисциплинам"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    ratings = db.query(PlayerRating).options(
        joinedload(PlayerRating.discipline)
    ).filter(PlayerRating.user_id == user_id).all()
    
    rating_summaries = []
    for rating in ratings:
        rating_summaries.append(UserRatingSummary(
            discipline_id=rating.discipline_id,
            discipline_name=rating.discipline.name,
            discipline_slug=rating.discipline.slug,
            discipline_icon=rating.discipline.icon,
            elo=rating.elo,
            level=rating.level,
            games_played=rating.games_played,
            wins=rating.wins,
            losses=rating.losses,
            win_rate=rating.win_rate,
            progress_to_next_level=rating.progress_to_next_level
        ))
    
    return {
        "user_id": user_id,
        "username": user.username,
        "ratings": rating_summaries,
        "total_ratings": len(rating_summaries)
    }


@router.get("/users/{user_id}/rating/{discipline_slug}", response_model=PlayerRatingResponse)
async def get_user_rating(
    user_id: int,
    discipline_slug: str,
    db: Session = Depends(get_db)
):
    """Получить рейтинг пользователя по конкретной дисциплине"""
    disc = db.query(Discipline).filter(Discipline.slug == discipline_slug).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    
    rating = db.query(PlayerRating).filter(
        PlayerRating.user_id == user_id,
        PlayerRating.discipline_id == disc.id
    ).first()
    
    if not rating:
        # Возвращаем дефолтный рейтинг
        return PlayerRatingResponse(
            id=0,
            user_id=user_id,
            discipline_id=disc.id,
            elo=BASE_ELO,
            level=1,
            games_played=0,
            wins=0,
            losses=0,
            draws=0,
            peak_elo=BASE_ELO,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            win_rate=0.0,
            progress_to_next_level=0.0
        )
    
    return rating


@router.get("/users/{user_id}/rating/{discipline_slug}/history", response_model=RatingHistoryResponse)
async def get_rating_history(
    user_id: int,
    discipline_slug: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Получить историю изменений рейтинга пользователя"""
    disc = db.query(Discipline).filter(Discipline.slug == discipline_slug).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    
    changes = db.query(RatingChange).filter(
        RatingChange.user_id == user_id,
        RatingChange.discipline_id == disc.id
    ).order_by(RatingChange.created_at.desc()).limit(limit).all()
    
    return {
        "user_id": user_id,
        "discipline": discipline_slug,
        "items": changes,
        "total": len(changes)
    }


# ==================== МАТЧМЕЙКИНГ ====================

@router.post("/matchmaking/queue", response_model=MatchmakingQueueResponse)
async def join_matchmaking_queue(
    request: Request,
    discipline: str = Query(..., description="Slug дисциплины"),
    game_type: str = Query("1v1", description="Тип матча: 1v1, 2v2, 5v5"),
    db: Session = Depends(get_db)
):
    """Встать в очередь матчмейкинга"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    # Получаем или создаём рейтинг пользователя
    rating = get_or_create_rating(db, user.id, disc.id)
    
    # Проверяем, не в очереди ли уже
    existing = db.query(MatchmakingQueue).filter(
        MatchmakingQueue.user_id == user.id,
        MatchmakingQueue.status == "waiting"
    ).first()
    
    if existing:
        wait_time = (datetime.utcnow() - existing.queued_at).total_seconds()
        return MatchmakingQueueResponse(
            status="waiting",
            game_type=existing.game_type,
            elo=existing.elo,
            queued_at=existing.queued_at,
            wait_time=int(wait_time)
        )
    
    # Создаём запись в очереди
    queue_entry = MatchmakingQueue(
        user_id=user.id,
        discipline_id=disc.id,
        game_type=game_type,
        elo=rating.elo
    )
    db.add(queue_entry)
    db.commit()
    db.refresh(queue_entry)
    
    # TODO: Запустить фоновую задачу поиска матча
    # asyncio.create_task(matchmaking_service.find_match(queue_entry))
    
    return MatchmakingQueueResponse(
        status="waiting",
        game_type=game_type,
        elo=rating.elo,
        queued_at=queue_entry.queued_at,
        wait_time=0,
        estimated_time=300  # 5 минут预估
    )


@router.get("/matchmaking/status", response_model=MatchmakingQueueResponse)
async def get_matchmaking_status(
    request: Request,
    db: Session = Depends(get_db)
):
    """Получить статус очереди матчмейкинга"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    queue_entry = db.query(MatchmakingQueue).filter(
        MatchmakingQueue.user_id == user.id,
        MatchmakingQueue.status.in_(["waiting", "found"])
    ).order_by(MatchmakingQueue.queued_at.desc()).first()
    
    if not queue_entry:
        raise HTTPException(status_code=404, detail="Вы не в очереди")
    
    wait_time = (datetime.utcnow() - queue_entry.queued_at).total_seconds()
    
    return MatchmakingQueueResponse(
        status=queue_entry.status,
        game_type=queue_entry.game_type,
        elo=queue_entry.elo,
        queued_at=queue_entry.queued_at,
        wait_time=int(wait_time),
        estimated_time=None
    )


@router.delete("/matchmaking/queue")
async def leave_matchmaking_queue(
    request: Request,
    db: Session = Depends(get_db)
):
    """Выйти из очереди матчмейкинга"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    queue_entry = db.query(MatchmakingQueue).filter(
        MatchmakingQueue.user_id == user.id,
        MatchmakingQueue.status == "waiting"
    ).first()
    
    if queue_entry:
        queue_entry.status = "cancelled"
        db.commit()
    
    return {"status": "cancelled", "message": "Вы вышли из очереди"}


# ==================== ТУРНИРНЫЕ СЕТКИ (BRACKET) ====================

@router.get("/tournaments/{tournament_id}/bracket")
async def get_tournament_bracket(
    tournament_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить данные для отрисовки турнирной сетки.
    
    Возвращает структуру раундов с матчами для визуализации bracket.
    """
    tournament = db.query(Tournament).filter(
        Tournament.id == tournament_id
    ).options(
        joinedload(Tournament.discipline),
        joinedload(Tournament.participations).joinedload(TournamentParticipation.team)
    ).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Турнир не найден")
    
    # Получаем матчи с данными команд
    matches = db.query(Match).filter(
        Match.tournament_id == tournament_id
    ).options(
        joinedload(Match.team1).joinedload(TournamentParticipation.team),
        joinedload(Match.team2).joinedload(TournamentParticipation.team),
        joinedload(Match.winner).joinedload(TournamentParticipation.team)
    ).order_by(Match.round, Match.match_order).all()
    
    # Формируем структуру для frontend
    bracket_data = {
        "tournament": {
            "id": tournament.id,
            "name": tournament.name,
            "format": tournament.format,
            "status": tournament.status,
            "discipline": tournament.discipline.name if tournament.discipline else None
        },
        "rounds": []
    }
    
    # Группируем матчи по раундам
    current_round = None
    round_data = None
    
    for match in matches:
        if match.round != current_round:
            if round_data:
                bracket_data["rounds"].append(round_data)
            
            current_round = match.round
            round_data = {
                "name": current_round,
                "matches": []
            }
        
        round_data["matches"].append({
            "id": match.id,
            "team1": {
                "id": match.team1.id if match.team1 else None,
                "name": match.team1.team.name if match.team1 and match.team1.team else "TBD",
                "score": match.team1_score,
                "logo": match.team1.team.logo_url if match.team1 and match.team1.team else None
            } if match.team1 else None,
            "team2": {
                "id": match.team2.id if match.team2 else None,
                "name": match.team2.team.name if match.team2 and match.team2.team else "TBD",
                "score": match.team2_score,
                "logo": match.team2.team.logo_url if match.team2 and match.team2.team else None
            } if match.team2 else None,
            "winner_id": match.winner.id if match.winner else None,
            "status": match.status,
            "next_match_id": match.next_match_id,
            "scheduled_at": match.scheduled_at.isoformat() if match.scheduled_at else None
        })
    
    if round_data:
        bracket_data["rounds"].append(round_data)
    
    return bracket_data


@router.get("/matches/{match_id}")
async def get_match_details(
    match_id: int,
    db: Session = Depends(get_db)
):
    """Получить детали матча"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Матч не найден")
    
    return {
        "id": match.id,
        "tournament_id": match.tournament_id,
        "round": match.round,
        "status": match.status,
        "team1_score": match.team1_score,
        "team2_score": match.team2_score,
        "scheduled_at": match.scheduled_at.isoformat() if match.scheduled_at else None,
        "created_at": match.created_at.isoformat()
    }
