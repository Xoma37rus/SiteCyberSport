"""
Ладдеры — система ежедневных рейтинговых соревнований
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from typing import Optional

from models import get_db, User, Discipline, Team, PlayerRating
from auth import get_current_user_from_cookie
from extended_models import Ladder, LadderParticipant, LadderMatch, create_extended_tables
from utils import generate_csrf_token, validate_csrf_token, get_or_create_rating

router = APIRouter(prefix="/ladders", tags=["ladders"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def ladders_page(request: Request, db: Session = Depends(get_db)):
    """Страница всех ладдеров"""
    current_user = get_current_user_from_cookie(request, db)

    now = datetime.utcnow()
    active = db.query(Ladder).options(
        joinedload(Ladder.discipline)
    ).filter(
        Ladder.status == "active",
        Ladder.end_date > now
    ).order_by(Ladder.start_date.desc()).all()

    upcoming = db.query(Ladder).options(
        joinedload(Ladder.discipline)
    ).filter(
        Ladder.status == "upcoming",
        Ladder.start_date > now
    ).order_by(Ladder.start_date).all()

    completed = db.query(Ladder).options(
        joinedload(Ladder.discipline)
    ).filter(
        Ladder.status == "completed"
    ).order_by(Ladder.end_date.desc()).limit(10).all()

    return templates.TemplateResponse("ladders.html", {
        "request": request,
        "current_user": current_user,
        "active_ladders": active,
        "upcoming_ladders": upcoming,
        "completed_ladders": completed,
    })


@router.get("/{ladder_id}", response_class=HTMLResponse)
async def ladder_detail(ladder_id: int, request: Request, db: Session = Depends(get_db)):
    """Детальная страница ладдера"""
    current_user = get_current_user_from_cookie(request, db)

    ladder = db.query(Ladder).options(
        joinedload(Ladder.discipline),
        joinedload(Ladder.participants).joinedload(LadderParticipant.user)
    ).filter(Ladder.id == ladder_id).first()

    if not ladder:
        raise HTTPException(status_code=404, detail="Ладдер не найден")

    # Сортируем участников по позиции
    participants = sorted(ladder.participants, key=lambda p: p.current_position)

    # Текущие матчи пользователя
    user_matches = []
    if current_user:
        user_participation = next(
            (p for p in ladder.participants if p.user_id == current_user.id), None
        )
        if user_participation:
            user_matches = db.query(LadderMatch).filter(
                LadderMatch.ladder_id == ladder_id,
                (LadderMatch.challenger_id == user_participation.id) |
                (LadderMatch.opponent_id == user_participation.id),
                LadderMatch.status == "pending"
            ).all()

    is_participant = current_user and any(
        p.user_id == current_user.id for p in ladder.participants
    )

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("ladder_detail.html", {
        "request": request,
        "current_user": current_user,
        "ladder": ladder,
        "participants": participants,
        "user_matches": user_matches,
        "is_participant": is_participant,
        "csrf_token": csrf_token,
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    return response


@router.post("/{ladder_id}/join")
async def join_ladder(
    ladder_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Присоединиться к ладдеру"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return JSONResponse({"error": "Требуется авторизация"}, status_code=401)

    ladder = db.query(Ladder).filter(Ladder.id == ladder_id).first()
    if not ladder:
        raise HTTPException(status_code=404, detail="Ладдер не найден")

    if ladder.status != "upcoming" and ladder.status != "active":
        return JSONResponse({"error": "Ладдер недоступен"}, status_code=400)

    # Проверка дубликата
    existing = db.query(LadderParticipant).filter(
        LadderParticipant.ladder_id == ladder_id,
        LadderParticipant.user_id == current_user.id
    ).first()
    if existing:
        return JSONResponse({"error": "Вы уже участвуете"}, status_code=400)

    # Проверка лимита
    count = db.query(LadderParticipant).filter(
        LadderParticipant.ladder_id == ladder_id
    ).count()
    if count >= ladder.max_participants:
        return JSONResponse({"error": "Ладдер заполнен"}, status_code=400)

    # Проверка ELO
    rating = db.query(PlayerRating).filter(
        PlayerRating.user_id == current_user.id,
        PlayerRating.discipline_id == ladder.discipline_id
    ).first()
    elo = rating.elo if rating else 1000

    if elo < ladder.entry_elo_min or elo > ladder.entry_elo_max:
        return JSONResponse({
            "error": f"Ваш ELO ({elo}) не подходит. Требуется: {ladder.entry_elo_min}-{ladder.entry_elo_max}"
        }, status_code=400)

    participant = LadderParticipant(
        ladder_id=ladder_id,
        user_id=current_user.id,
        elo_at_start=elo,
        current_position=count + 1,
    )
    db.add(participant)
    db.commit()

    return {"status": "joined", "message": "Вы присоединились к ладдеру"}


@router.post("/{ladder_id}/challenge")
async def challenge_opponent(
    ladder_id: int,
    request: Request,
    opponent_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Бросить вызов сопернику"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return JSONResponse({"error": "Требуется авторизация"}, status_code=401)

    ladder = db.query(Ladder).filter(Ladder.id == ladder_id).first()
    if not ladder or ladder.status != "active":
        return JSONResponse({"error": "Ладдер не активен"}, status_code=400)

    challenger = db.query(LadderParticipant).filter(
        LadderParticipant.ladder_id == ladder_id,
        LadderParticipant.user_id == current_user.id
    ).first()
    if not challenger:
        return JSONResponse({"error": "Вы не участник ладдера"}, status_code=400)

    opponent = db.query(LadderParticipant).filter(
        LadderParticipant.id == opponent_id,
        LadderParticipant.ladder_id == ladder_id
    ).first()
    if not opponent:
        return JSONResponse({"error": "Соперник не найден"}, status_code=404)

    # Проверка на уже существующий активный матч
    existing = db.query(LadderMatch).filter(
        LadderMatch.ladder_id == ladder_id,
        LadderMatch.status == "pending",
        (
            (LadderMatch.challenger_id == challenger.id) |
            (LadderMatch.opponent_id == challenger.id)
        )
    ).first()
    if existing:
        return JSONResponse({"error": "У вас уже есть активный вызов"}, status_code=400)

    match = LadderMatch(
        ladder_id=ladder_id,
        challenger_id=challenger.id,
        opponent_id=opponent.id,
        status="pending",
    )
    db.add(match)
    db.commit()

    return {"status": "challenged", "message": "Вызов отправлен"}


@router.post("/matches/{match_id}/report")
async def report_ladder_result(
    match_id: int,
    request: Request,
    challenger_score: int = Form(...),
    opponent_score: int = Form(...),
    db: Session = Depends(get_db)
):
    """Сообщить результат матча ладдера"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return JSONResponse({"error": "Требуется авторизация"}, status_code=401)

    match = db.query(LadderMatch).filter(LadderMatch.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Матч не найден")

    if match.status != "pending":
        return JSONResponse({"error": "Матч уже завершён"}, status_code=400)

    match.challenger_score = challenger_score
    match.opponent_score = opponent_score
    match.status = "completed"
    match.completed_at = datetime.utcnow()
    match.reported_by = current_user.id
    match.verified = True  # TODO: система оспаривания

    # Определяем победителя
    if challenger_score > opponent_score:
        match.winner_id = match.challenger_id
    elif opponent_score > challenger_score:
        match.winner_id = match.opponent_id
    else:
        match.winner_id = None  # Ничья

    # Обновляем статистику участников
    challenger = db.query(LadderParticipant).filter(
        LadderParticipant.id == match.challenger_id
    ).first()
    opponent = db.query(LadderParticipant).filter(
        LadderParticipant.id == match.opponent_id
    ).first()

    if match.winner_id == match.challenger_id:
        challenger.wins += 1
        opponent.losses += 1
    elif match.winner_id == match.opponent_id:
        opponent.wins += 1
        challenger.losses += 1

    # Пересчёт позиций
    recalculate_ladder_positions(db, match.ladder_id)
    db.commit()

    return {"status": "reported", "message": "Результат сохранён"}


def recalculate_ladder_positions(db: Session, ladder_id: int):
    """Пересчёт позиций в ладдере по wins/losses"""
    participants = db.query(LadderParticipant).filter(
        LadderParticipant.ladder_id == ladder_id
    ).all()

    # Сортировка: больше побед, меньше поражений
    participants.sort(key=lambda p: (p.wins, -p.losses), reverse=True)

    for i, p in enumerate(participants):
        p.current_position = i + 1


def create_daily_ladders(db: Session):
    """Создать ежедневные ладдеры (запускается cron'ом или при старте)"""
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)

    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()

    for disc in disciplines:
        # Проверяем, есть ли уже ладдер на сегодня
        existing = db.query(Ladder).filter(
            Ladder.discipline_id == disc.id,
            Ladder.start_date >= datetime(today.year, today.month, today.day),
            Ladder.start_date < datetime(tomorrow.year, tomorrow.month, tomorrow.day),
        ).first()

        if not existing:
            ladder = Ladder(
                name=f"Daily {disc.name} — {today.strftime('%d.%m.%Y')}",
                discipline_id=disc.id,
                game_type="1v1",
                start_date=datetime(today.year, today.month, today.day, 18, 0),
                end_date=datetime(tomorrow.year, tomorrow.month, tomorrow.day, 2, 0),
                status="upcoming",
                max_participants=32,
                entry_elo_min=0,
                entry_elo_max=9999,
                prize_description="Слава и +50 ELO победителю",
            )
            db.add(ladder)

    db.commit()
