"""
API Endpoints для EasyCyberPro
REST API для frontend-разработки и мобильных приложений
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from models import get_db, User, News, Discipline, Team, Tournament
from schemas import (
    NewsResponse, NewsListResponse,
    DisciplineResponse, DisciplineListResponse,
    TeamResponse, TeamListResponse,
    TournamentResponse, TournamentListResponse,
    UserResponse, HealthResponse
)

router = APIRouter(prefix="/api/v1", tags=["API"])


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
