from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
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

    teams = db.query(Team).filter(
        Team.discipline_id == discipline.id,
        Team.is_active == True
    ).order_by(Team.rating.desc()).all()

    total_matches = sum(t.wins + t.losses for t in teams)
    total_players = db.query(TeamMember).filter(
        TeamMember.team_id.in_([t.id for t in teams])
    ).count() if teams else 0

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
