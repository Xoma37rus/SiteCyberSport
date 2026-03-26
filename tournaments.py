"""
Турниры: Страницы для пользователей
Просмотр турниров, регистрация команд, архив
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Form, Cookie, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from models import get_db, Tournament, Discipline, Team, TournamentParticipation, User
from datetime import datetime
from jose import jwt, JWTError
from config import settings
from utils import validate_csrf_token, generate_csrf_token

router = APIRouter(tags=["tournaments"])
templates = Jinja2Templates(directory="templates")


def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Получить текущего пользователя из cookie"""
    token = request.cookies.get("access_token")
    if not token:
        return None

    if token.startswith("Bearer "):
        token = token[7:]

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        if user and user.is_verified:
            return user
    except JWTError:
        pass
    return None


def get_user_teams(db: Session, user_id: int):
    """Получить команды пользователя"""
    # Команды где пользователь является капитаном
    captain_teams = db.query(Team).filter(Team.captain_id == user_id, Team.is_active == True).all()
    return captain_teams


@router.get("/tournaments", response_class=HTMLResponse)
async def tournaments_page(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    search: str = None,
    discipline: str = None,
    db: Session = Depends(get_db)
):
    """Страница всех турниров с разделением на активные и архив, пагинацией и фильтрами"""
    current_time = datetime.utcnow()

    # Базовые запросы с joinedload для избежания N+1
    active_query = db.query(Tournament).options(
        joinedload(Tournament.discipline)
    ).filter(
        Tournament.status.in_(["registration", "active", "upcoming"])
    )
    archived_query = db.query(Tournament).options(
        joinedload(Tournament.discipline)
    ).filter(
        Tournament.status.in_(["completed", "cancelled"])
    )

    # Поиск по названию
    if search:
        active_query = active_query.filter(Tournament.name.ilike(f"%{search}%"))
        archived_query = archived_query.filter(Tournament.name.ilike(f"%{search}%"))

    # Фильтр по дисциплине
    if discipline:
        disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
        if disc:
            active_query = active_query.filter(Tournament.discipline_id == disc.id)
            archived_query = archived_query.filter(Tournament.discipline_id == disc.id)

    # Получаем общее количество
    total_active = active_query.count()
    total_archived = archived_query.count()

    # Применяем пагинацию
    offset = (page - 1) * limit
    active_tournaments = active_query.order_by(Tournament.start_date.asc()).offset(offset).limit(limit).all()
    archived_tournaments = archived_query.order_by(Tournament.start_date.desc()).offset(offset).limit(limit).all()

    # Получаем все дисциплины для фильтра
    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()

    return templates.TemplateResponse("tournaments.html", {
        "request": request,
        "active_tournaments": active_tournaments,
        "archived_tournaments": archived_tournaments,
        "disciplines": disciplines,
        "selected_discipline": discipline or "",
        "search_query": search or "",
        "page": page,
        "limit": limit,
        "total_active": total_active,
        "total_archived": total_archived,
        "pages": (max(total_active, total_archived) + limit - 1) // limit
    })


@router.get("/tournament/{tournament_id}", response_class=HTMLResponse)
async def tournament_detail(
    request: Request,
    tournament_id: int,
    db: Session = Depends(get_db)
):
    """Страница отдельного турнира с возможностью регистрации"""
    tournament = db.query(Tournament).options(
        joinedload(Tournament.discipline),
        joinedload(Tournament.participations).joinedload(TournamentParticipation.team).joinedload(Team.captain),
        joinedload(Tournament.participations).joinedload(TournamentParticipation.team).joinedload(Team.discipline)
    ).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Турнир не найден")

    # Получаем текущего пользователя
    current_user = get_current_user_from_cookie(request, db)

    # Получаем подтверждённые заявки
    confirmed_participations = db.query(TournamentParticipation).filter(
        TournamentParticipation.tournament_id == tournament_id,
        TournamentParticipation.is_confirmed == True
    ).all()

    # Получаем все заявки для проверки, зарегистрировался ли пользователь
    user_participations = []
    user_teams_ids = []
    if current_user:
        user_teams = get_user_teams(db, current_user.id)
        user_teams_ids = [t.id for t in user_teams]
        user_participations = db.query(TournamentParticipation).filter(
            TournamentParticipation.tournament_id == tournament_id,
            TournamentParticipation.team_id.in_(user_teams_ids) if user_teams_ids else False
        ).all()

    # Получаем команды пользователя для формы регистрации
    user_teams = get_user_teams(db, current_user.id) if current_user else []

    # Проверяем, может ли пользователь зарегистрироваться
    can_register = False
    already_registered = False
    registration_error = None

    if current_user:
        if tournament.status != "registration":
            registration_error = "Регистрация закрыта"
        elif tournament.registered_teams_count >= tournament.max_teams:
            registration_error = "Все места заняты"
        elif tournament.registration_deadline and tournament.registration_deadline < datetime.utcnow():
            registration_error = "Регистрация завершена"
        else:
            can_register = True
            # Проверяем, не зарегистрирована ли уже команда пользователя
            for participation in user_participations:
                already_registered = True
                break
    else:
        registration_error = "Требуется авторизация"

    return templates.TemplateResponse("tournament_detail.html", {
        "request": request,
        "tournament": tournament,
        "participations": confirmed_participations,
        "current_user": current_user,
        "user_teams": user_teams,
        "can_register": can_register,
        "already_registered": already_registered,
        "registration_error": registration_error,
        "csrf_token": generate_csrf_token()
    })


@router.post("/tournament/{tournament_id}/register")
async def register_for_tournament(
    request: Request,
    tournament_id: int,
    team_id: int = Form(...),
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    """Регистрация команды на турнир"""
    current_user = get_current_user_from_cookie(request, db)

    if not current_user:
        return RedirectResponse("/login", status_code=303)

    # CSRF проверка
    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        return RedirectResponse("/tournaments", status_code=303)

    # Проверка статуса турнира
    if tournament.status != "registration":
        return RedirectResponse(f"/tournament/{tournament_id}", status_code=303)

    # Проверка команды
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        return RedirectResponse(f"/tournament/{tournament_id}", status_code=303)

    # Проверка, что пользователь является капитаном команды
    if team.captain_id != current_user.id:
        return RedirectResponse(f"/tournament/{tournament_id}", status_code=303)

    # Проверка, не зарегистрирована ли уже команда
    existing = db.query(TournamentParticipation).filter(
        TournamentParticipation.tournament_id == tournament_id,
        TournamentParticipation.team_id == team_id
    ).first()

    if existing:
        return RedirectResponse(f"/tournament/{tournament_id}", status_code=303)

    # Проверка заполненности мест
    if tournament.registered_teams_count >= tournament.max_teams:
        return RedirectResponse(f"/tournament/{tournament_id}", status_code=303)

    # Создание заявки
    participation = TournamentParticipation(
        tournament_id=tournament_id,
        team_id=team_id,
        user_id=current_user.id,
        is_confirmed=False  # Требуется подтверждение администратора
    )
    db.add(participation)
    db.commit()

    return RedirectResponse(f"/tournament/{tournament_id}?registered=1", status_code=303)


@router.post("/tournament/{tournament_id}/cancel-registration")
async def cancel_registration(
    request: Request,
    tournament_id: int,
    team_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Отмена регистрации команды на турнир"""
    current_user = get_current_user_from_cookie(request, db)

    if not current_user:
        return RedirectResponse("/login", status_code=303)

    participation = db.query(TournamentParticipation).filter(
        TournamentParticipation.tournament_id == tournament_id,
        TournamentParticipation.team_id == team_id,
        TournamentParticipation.user_id == current_user.id
    ).first()

    if participation:
        db.delete(participation)
        db.commit()

    return RedirectResponse(f"/tournament/{tournament_id}", status_code=303)
