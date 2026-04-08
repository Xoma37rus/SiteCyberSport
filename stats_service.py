"""
Stats Service — расширенная статистика игроков
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional, List
import csv
import io

from models import get_db, User, PlayerRating, RatingChange, Match, TournamentParticipation, Tournament, Discipline
from auth import get_current_user_from_cookie
from utils import get_level_by_elo

router = APIRouter(prefix="/stats", tags=["stats"])
templates = Jinja2Templates(directory="templates")


@router.get("/api/{user_id}")
async def get_user_stats(
    user_id: int,
    request: Request,
    discipline: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """API: расширенная статистика пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    stats = {
        "user": {
            "id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at.isoformat(),
        },
        "overview": {
            "total_matches": user.total_matches,
            "total_wins": user.total_wins,
            "total_losses": user.total_losses,
            "win_rate": round(user.total_wins / user.total_matches * 100, 1) if user.total_matches > 0 else 0,
        },
        "disciplines": [],
        "elo_history": [],
        "recent_matches": [],
    }

    # Рейтинги по дисциплинам
    disc_filter = []
    if discipline:
        disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
        if disc:
            disc_filter = [disc.id]

    ratings = db.query(PlayerRating).filter(
        PlayerRating.user_id == user_id,
        PlayerRating.discipline_id.in_(disc_filter) if disc_filter else True
    ).all()

    for rating in ratings:
        disc = db.query(Discipline).filter(Discipline.id == rating.discipline_id).first()
        stats["disciplines"].append({
            "discipline": disc.name if disc else "Unknown",
            "discipline_slug": disc.slug if disc else "unknown",
            "elo": rating.elo,
            "level": rating.level,
            "games_played": rating.games_played,
            "wins": rating.wins,
            "losses": rating.losses,
            "draws": rating.draws,
            "win_rate": round(rating.wins / rating.games_played * 100, 1) if rating.games_played > 0 else 0,
            "peak_elo": rating.peak_elo,
            "progress_to_next_level": rating.progress_to_next_level,
        })

    # ELO история (последние 50 изменений)
    elo_changes = db.query(RatingChange).filter(
        RatingChange.user_id == user_id
    ).order_by(RatingChange.created_at.desc()).limit(50).all()

    stats["elo_history"] = [
        {
            "date": change.created_at.isoformat(),
            "elo_after": change.elo_after,
            "elo_change": change.elo_change,
            "reason": change.reason,
        }
        for change in elo_changes
    ]

    # Последние матчи
    participations = db.query(TournamentParticipation).filter(
        TournamentParticipation.user_id == user_id
    ).order_by(TournamentParticipation.registered_at.desc()).limit(10).all()

    for part in participations:
        tournament = db.query(Tournament).filter(Tournament.id == part.tournament_id).first()
        stats["recent_matches"].append({
            "tournament": tournament.name if tournament else "Unknown",
            "date": part.registered_at.isoformat(),
            "status": tournament.status if tournament else "unknown",
        })

    return stats


@router.get("/api/{user_id}/elo-history")
async def get_elo_history(
    user_id: int,
    discipline: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """API: история ELO для графика"""
    query = db.query(RatingChange).filter(
        RatingChange.user_id == user_id
    )

    if discipline:
        disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
        if disc:
            query = query.filter(RatingChange.discipline_id == disc.id)

    changes = query.order_by(RatingChange.created_at).limit(limit).all()

    return [
        {
            "date": c.created_at.strftime("%Y-%m-%d"),
            "elo": c.elo_after,
            "change": c.elo_change,
        }
        for c in changes
    ]


@router.get("/api/{user_id}/export")
async def export_stats_csv(
    user_id: int,
    request: Request,
    discipline: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """API: экспорт статистики в CSV"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовок
    writer.writerow(["EasyCyberPro — Статистика пользователя"])
    writer.writerow(["Пользователь", user.username])
    writer.writerow(["Дата экспорта", datetime.utcnow().strftime("%Y-%m-%d %H:%M")])
    writer.writerow([])

    # Общая статистика
    writer.writerow(["Общая статистика"])
    writer.writerow(["Метрика", "Значение"])
    writer.writerow(["Всего матчей", user.total_matches])
    writer.writerow(["Побед", user.total_wins])
    writer.writerow(["Поражений", user.total_losses])
    win_rate = round(user.total_wins / user.total_matches * 100, 1) if user.total_matches > 0 else 0
    writer.writerow(["Винрейт", f"{win_rate}%"])
    writer.writerow([])

    # Рейтинги по дисциплинам
    writer.writerow(["Рейтинги по дисциплинам"])
    writer.writerow(["Дисциплина", "ELO", "Уровень", "Игры", "Победы", "Поражения", "Винрейт", "Пик ELO"])

    ratings = db.query(PlayerRating).filter(PlayerRating.user_id == user_id).all()
    for rating in ratings:
        disc = db.query(Discipline).filter(Discipline.id == rating.discipline_id).first()
        wr = round(rating.wins / rating.games_played * 100, 1) if rating.games_played > 0 else 0
        writer.writerow([
            disc.name if disc else "Unknown",
            rating.elo,
            rating.level,
            rating.games_played,
            rating.wins,
            rating.losses,
            f"{wr}%",
            rating.peak_elo,
        ])

    # История ELO
    writer.writerow([])
    writer.writerow(["История ELO"])
    writer.writerow(["Дата", "ELO после", "Изменение", "Причина"])

    changes = db.query(RatingChange).filter(
        RatingChange.user_id == user_id
    ).order_by(RatingChange.created_at.desc()).limit(200).all()

    for change in changes:
        writer.writerow([
            change.created_at.strftime("%Y-%m-%d %H:%M"),
            change.elo_after,
            change.elo_change,
            change.reason,
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=easycyberpro_stats_{user.username}_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
    )


@router.get("/{user_id}")
async def user_stats_page(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """HTML страница статистики"""
    current_user = get_current_user_from_cookie(request, db)
    target_user = db.query(User).filter(User.id == user_id).first()

    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Получаем рейтинги
    ratings = db.query(PlayerRating).filter(
        PlayerRating.user_id == user_id
    ).all()

    # ELO история для графика
    elo_history = db.query(RatingChange).filter(
        RatingChange.user_id == user_id
    ).order_by(RatingChange.created_at).limit(200).all()

    return templates.TemplateResponse("user_stats.html", {
        "request": request,
        "current_user": current_user,
        "target_user": target_user,
        "ratings": ratings,
        "elo_history": elo_history,
    })
