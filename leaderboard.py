"""
Leaderboard - Таблица лидеров
Показывает только тех пользователей, у которых отмечена соответствующая дисциплина в личном кабинете
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from models import get_db, Discipline, PlayerRating, User, user_disciplines
from auth import get_current_user_from_cookie
from utils import get_or_create_rating
from extended_models import StudentRating

router = APIRouter(tags=["leaderboard"])
templates = Jinja2Templates(directory="templates")


def ensure_users_with_discipline_have_ratings(db: Session, discipline_id: int):
    """Создать рейтинги только для учеников, у которых отмечена эта дисциплина"""
    # Находим только учеников с данной дисциплиной
    students_with_discipline = db.query(User).join(
        user_disciplines, User.id == user_disciplines.c.user_id
    ).filter(
        user_disciplines.c.discipline_id == discipline_id,
        User.is_active == True,
        User.role.like('student%')  # Только ученики
    ).all()

    for user in students_with_discipline:
        get_or_create_rating(db, user.id, discipline_id)
    db.commit()


@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(
    request: Request,
    discipline: str = "dota2",
    db: Session = Depends(get_db)
):
    """Страница таблицы лидеров по дисциплине — только пользователи с отмеченной дисциплиной"""
    current_user = get_current_user_from_cookie(request, db)

    # Получаем дисциплину
    disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    # Получаем все дисциплины для переключателя
    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()

    # Создаём рейтинги только для учеников с этой дисциплиной
    ensure_users_with_discipline_have_ratings(db, disc.id)

    # Получаем рейтинги ТОЛЬКО для учеников (роль начинается с 'student'), у которых есть эта дисциплина
    ratings = db.query(PlayerRating).join(
        User, PlayerRating.user_id == User.id
    ).join(
        user_disciplines, User.id == user_disciplines.c.user_id
    ).options(
        joinedload(PlayerRating.user)
    ).filter(
        PlayerRating.discipline_id == disc.id,
        user_disciplines.c.discipline_id == disc.id,
        User.is_active == True,
        User.role.like('student%')  # Только ученики
    ).order_by(PlayerRating.elo.desc()).limit(100).all()

    # Получаем рейтинг текущего пользователя (если он ученик и у него есть эта дисциплина)
    user_rating = None
    user_rank = None
    if current_user and current_user.role and current_user.role.startswith('student'):
        user_rating = db.query(PlayerRating).filter(
            PlayerRating.user_id == current_user.id,
            PlayerRating.discipline_id == disc.id
        ).first()

        # Определяем ранг пользователя (среди учеников с этой дисциплиной)
        if user_rating:
            user_rank = db.query(PlayerRating).join(
                User, PlayerRating.user_id == User.id
            ).join(
                user_disciplines, User.id == user_disciplines.c.user_id
            ).filter(
                PlayerRating.discipline_id == disc.id,
                user_disciplines.c.discipline_id == disc.id,
                User.is_active == True,
                User.role.like('student%'),
                PlayerRating.elo > user_rating.elo
            ).count() + 1

    return templates.TemplateResponse("leaderboard.html", {
        "request": request,
        "current_user": current_user,
        "disciplines": disciplines,
        "current_discipline": disc,
        "ratings": ratings,
        "user_rating": user_rating,
        "user_rank": user_rank
    })


@router.get("/ratings", response_class=HTMLResponse)
async def all_leaderboards_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """Страница со всеми таблицами лидеров"""
    current_user = get_current_user_from_cookie(request, db)
    
    # Получаем все дисциплины
    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
    
    # Получаем топ игроков для каждой дисциплины
    leaderboard_data = []
    for disc in disciplines:
        top_players = db.query(PlayerRating).options(
            joinedload(PlayerRating.user)
        ).filter(
            PlayerRating.discipline_id == disc.id
        ).order_by(PlayerRating.elo.desc()).limit(3).all()
        
        leaderboard_data.append({
            "discipline": disc,
            "top_players": top_players,
            "total_players": db.query(PlayerRating).filter(
                PlayerRating.discipline_id == disc.id
            ).count()
        })
    
    return templates.TemplateResponse("leaderboards.html", {
        "request": request,
        "current_user": current_user,
        "leaderboard_data": leaderboard_data
    })
