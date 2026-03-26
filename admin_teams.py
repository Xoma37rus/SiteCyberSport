"""
Админ-панель: Управление командами
CRUD операции для команд
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import get_db, Team, Discipline, User
from utils import generate_csrf_token, validate_csrf_token, create_flash_message
from admin import get_current_admin_user, require_admin, log_admin_action

router = APIRouter(prefix="/admin/teams", tags=["admin_teams"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def admin_teams_list(
    request: Request,
    page: int = 1,
    limit: int = 20,
    discipline: str = None,
    db: Session = Depends(get_db)
):
    """Список всех команд с фильтрацией и пагинацией"""
    admin = require_admin(request, db)

    query = db.query(Team)

    # Фильтр по дисциплине
    if discipline:
        disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
        if disc:
            query = query.filter(Team.discipline_id == disc.id)

    total = query.count()
    offset = (page - 1) * limit
    teams = query.order_by(Team.rating.desc()).offset(offset).limit(limit).all()

    # Получаем все дисциплины для фильтра
    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()

    flash_data = None
    flash_cookie = request.cookies.get("flash_message")
    if flash_cookie:
        from utils import parse_flash_message
        flash_data = parse_flash_message(flash_cookie)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("admin/teams_list.html", {
        "request": request,
        "admin": admin,
        "teams": teams,
        "disciplines": disciplines,
        "selected_discipline": discipline or "",
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit,
        "flash": flash_data,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    if flash_cookie:
        response.delete_cookie("flash_message")
    return response


@router.get("/create", response_class=HTMLResponse)
async def admin_teams_create_page(request: Request, db: Session = Depends(get_db)):
    """Страница создания команды"""
    admin = require_admin(request, db)

    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
    users = db.query(User).filter(User.is_active == True).order_by(User.username).all()

    csrf_token = generate_csrf_token()
    return templates.TemplateResponse("admin/teams_form.html", {
        "request": request,
        "admin": admin,
        "disciplines": disciplines,
        "users": users,
        "team": None,
        "action": "create",
        "csrf_token": csrf_token
    })


@router.post("/create")
async def admin_teams_create(
    request: Request,
    name: str = Form(...),
    discipline_id: int = Form(...),
    captain_id: int = Form(None),
    description: str = Form(""),
    wins: int = Form(0),
    losses: int = Form(0),
    rating: float = Form(1000),
    is_active: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Создание новой команды"""
    admin = require_admin(request, db)

    # Проверка существующего названия
    existing = db.query(Team).filter(Team.name == name).first()
    if existing:
        disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
        users = db.query(User).filter(User.is_active == True).all()
        csrf_token = generate_csrf_token()
        return templates.TemplateResponse("admin/teams_form.html", {
            "request": request,
            "admin": admin,
            "disciplines": disciplines,
            "users": users,
            "team": None,
            "action": "create",
            "error": "Команда с таким названием уже существует",
            "csrf_token": csrf_token
        })

    # Создание команды
    team = Team(
        name=name,
        discipline_id=discipline_id,
        captain_id=captain_id if captain_id else None,
        description=description,
        wins=wins,
        losses=losses,
        rating=rating,
        is_active=is_active
    )
    db.add(team)
    db.commit()
    db.refresh(team)

    # Логирование
    log_admin_action(
        db, admin, "create",
        target_type="team",
        target_id=team.id,
        details=f"Created team: {name}",
        request=request
    )

    response = RedirectResponse("/admin/teams", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Команда {name} успешно создана",
        "success"
    ))
    return response


@router.get("/{team_id}/edit", response_class=HTMLResponse)
async def admin_teams_edit_page(
    request: Request,
    team_id: int,
    db: Session = Depends(get_db)
):
    """Страница редактирования команды"""
    admin = require_admin(request, db)

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Команда не найдена")

    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
    users = db.query(User).filter(User.is_active == True).order_by(User.username).all()

    csrf_token = generate_csrf_token()
    return templates.TemplateResponse("admin/teams_form.html", {
        "request": request,
        "admin": admin,
        "disciplines": disciplines,
        "users": users,
        "team": team,
        "action": "edit",
        "csrf_token": csrf_token
    })


@router.post("/{team_id}/update")
async def admin_teams_update(
    request: Request,
    team_id: int,
    name: str = Form(...),
    discipline_id: int = Form(...),
    captain_id: int = Form(None),
    description: str = Form(""),
    wins: int = Form(0),
    losses: int = Form(0),
    rating: float = Form(1000),
    is_active: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Обновление команды"""
    admin = require_admin(request, db)

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Команда не найдена")

    # Проверка названия (если изменилось)
    if team.name != name:
        existing = db.query(Team).filter(Team.name == name).first()
        if existing and existing.id != team_id:
            disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
            users = db.query(User).filter(User.is_active == True).all()
            csrf_token = generate_csrf_token()
            return templates.TemplateResponse("admin/teams_form.html", {
                "request": request,
                "admin": admin,
                "disciplines": disciplines,
                "users": users,
                "team": team,
                "action": "edit",
                "error": "Команда с таким названием уже существует",
                "csrf_token": csrf_token
            })

    # Сохранение изменений
    old_wins = team.wins
    old_losses = team.losses

    team.name = name
    team.discipline_id = discipline_id
    team.captain_id = captain_id if captain_id else None
    team.description = description
    team.wins = wins
    team.losses = losses
    team.rating = rating
    team.is_active = is_active

    db.commit()

    # Логирование
    log_admin_action(
        db, admin, "update",
        target_type="team",
        target_id=team.id,
        details=f"Updated team: {name} (wins: {old_wins}->{wins}, losses: {old_losses}->{losses})",
        request=request
    )

    response = RedirectResponse("/admin/teams", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Команда {name} успешно обновлена",
        "success"
    ))
    return response


@router.post("/{team_id}/delete")
async def admin_teams_delete(
    request: Request,
    team_id: int,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    """Удаление команды"""
    admin = require_admin(request, db)

    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Команда не найдена")

    team_name = team.name
    db.delete(team)
    db.commit()

    # Логирование
    log_admin_action(
        db, admin, "delete",
        target_type="team",
        target_id=team_id,
        details=f"Deleted team: {team_name}",
        request=request
    )

    response = RedirectResponse("/admin/teams", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Команда {team_name} удалена",
        "success"
    ))
    return response
