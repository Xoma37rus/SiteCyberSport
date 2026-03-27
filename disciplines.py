from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from models import get_db, Discipline, Team, TeamMember

router = APIRouter(tags=["disciplines"])
templates = Jinja2Templates(directory="templates")


@router.get("/discipline/{discipline_name}", response_class=HTMLResponse)
async def discipline_page(
    request: Request,
    discipline_name: str,
    db: Session = Depends(get_db)
):
    """Страница дисциплины с командами из БД"""
    discipline = db.query(Discipline).filter(Discipline.slug == discipline_name).first()

    if not discipline:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    # Исправление N+1: загружаем teams с members
    teams = db.query(Team).options(
        joinedload(Team.members)
    ).filter(
        Team.discipline_id == discipline.id,
        Team.is_active == True
    ).order_by(Team.rating.desc()).all()

    # Оптимизация: вычисляем статистику без дополнительных запросов
    total_matches = sum(t.wins + t.losses for t in teams)
    total_players = sum(len(t.members) for t in teams) if teams else 0

    top_team = teams[0] if teams else None

    return templates.TemplateResponse("discipline.html", {
        "request": request,
        "discipline": discipline,
        "teams": teams,
        "stats": {
            "total_matches": total_matches,
            "total_players": total_players,
            "avg_match_duration": "35 мин",
            "top_team": top_team.name if top_team else "N/A"
        }
    })
