"""
Leaderboard - Таблица лидеров
Страницы для просмотра рейтинга игроков по дисциплинам
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from models import get_db, Discipline, PlayerRating, User
from auth import get_current_user_from_cookie

router = APIRouter(tags=["leaderboard"])
templates = Jinja2Templates(directory="templates")


@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(
    request: Request,
    discipline: str = "dota2",
    db: Session = Depends(get_db)
):
    """Страница таблицы лидеров по дисциплине"""
    current_user = get_current_user_from_cookie(request, db)
    
    # Получаем дисциплину
    disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    
    # Получаем все дисциплины для переключателя
    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
    
    # Получаем топ игроков
    ratings = db.query(PlayerRating).options(
        joinedload(PlayerRating.user)
    ).filter(
        PlayerRating.discipline_id == disc.id
    ).order_by(PlayerRating.elo.desc()).limit(100).all()
    
    # Получаем рейтинг текущего пользователя
    user_rating = None
    user_rank = None
    if current_user:
        user_rating = db.query(PlayerRating).filter(
            PlayerRating.user_id == current_user.id,
            PlayerRating.discipline_id == disc.id
        ).first()
        
        # Определяем ранг пользователя
        if user_rating:
            user_rank = db.query(PlayerRating).filter(
                PlayerRating.discipline_id == disc.id,
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
