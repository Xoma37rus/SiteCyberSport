"""
Админ-панель: Управление турнирами
CRUD операции для турниров и управление заявками команд
"""

import logging
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from models import get_db, Tournament, Discipline, Team, TournamentParticipation, User
from utils import generate_csrf_token, validate_csrf_token, create_flash_message
from admin import get_current_admin_user, require_admin, log_admin_action
from datetime import datetime
from mailer import send_tournament_confirmation_email, send_tournament_rejection_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/tournaments", tags=["admin_tournaments"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def admin_tournaments_list(
    request: Request,
    page: int = 1,
    limit: int = 20,
    status: str = None,
    discipline: str = None,
    db: Session = Depends(get_db)
):
    """Список всех турниров с фильтрацией и пагинацией"""
    admin = require_admin(request, db)

    query = db.query(Tournament).options(
        joinedload(Tournament.discipline)
    )

    # Фильтр по статусу
    if status:
        query = query.filter(Tournament.status == status)

    # Фильтр по дисциплине
    if discipline:
        disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
        if disc:
            query = query.filter(Tournament.discipline_id == disc.id)

    total = query.count()
    offset = (page - 1) * limit
    tournaments = query.order_by(Tournament.start_date.desc()).offset(offset).limit(limit).all()

    # Получаем все дисциплины и статусы для фильтра
    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
    statuses = ["upcoming", "registration", "active", "completed", "cancelled"]

    flash_data = None
    flash_cookie = request.cookies.get("flash_message")
    if flash_cookie:
        from utils import parse_flash_message
        flash_data = parse_flash_message(flash_cookie)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("admin/tournaments_list.html", {
        "request": request,
        "admin": admin,
        "tournaments": tournaments,
        "disciplines": disciplines,
        "statuses": statuses,
        "selected_status": status or "",
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
async def admin_tournaments_create_page(request: Request, db: Session = Depends(get_db)):
    """Страница создания турнира"""
    admin = require_admin(request, db)

    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()

    csrf_token = generate_csrf_token()
    return templates.TemplateResponse("admin/tournaments_form.html", {
        "request": request,
        "admin": admin,
        "disciplines": disciplines,
        "tournament": None,
        "action": "create",
        "csrf_token": csrf_token
    })


@router.post("/create")
async def admin_tournaments_create(
    request: Request,
    name: str = Form(...),
    discipline_id: int = Form(...),
    description: str = Form(""),
    prize_pool: str = Form(""),
    max_teams: int = Form(16),
    registration_deadline_str: str = Form(""),
    start_date_str: str = Form(""),
    end_date_str: str = Form(""),
    status: str = Form("upcoming"),
    format: str = Form("single_elimination"),
    is_online: bool = Form(False),
    image_url: str = Form(""),
    db: Session = Depends(get_db)
):
    """Создание нового турнира"""
    admin = require_admin(request, db)

    # Парсинг дат
    registration_deadline = None
    start_date = None
    end_date = None

    if registration_deadline_str:
        try:
            registration_deadline = datetime.strptime(registration_deadline_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            pass

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            pass

    # Валидация дат
    if registration_deadline and start_date and registration_deadline >= start_date:
        disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
        csrf_token = generate_csrf_token()
        return templates.TemplateResponse("admin/tournaments_form.html", {
            "request": request,
            "admin": admin,
            "disciplines": disciplines,
            "tournament": None,
            "action": "create",
            "error": "Регистрация должна завершиться до начала турнира",
            "csrf_token": csrf_token
        })

    if start_date and end_date and start_date >= end_date:
        disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
        csrf_token = generate_csrf_token()
        return templates.TemplateResponse("admin/tournaments_form.html", {
            "request": request,
            "admin": admin,
            "disciplines": disciplines,
            "tournament": None,
            "action": "create",
            "error": "Дата начала должна быть раньше даты окончания",
            "csrf_token": csrf_token
        })

    # Создание турнира
    tournament = Tournament(
        name=name,
        discipline_id=discipline_id,
        description=description,
        prize_pool=prize_pool,
        max_teams=max_teams,
        registration_deadline=registration_deadline,
        start_date=start_date,
        end_date=end_date,
        status=status,
        format=format,
        is_online=is_online,
        image_url=image_url
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)

    # Логирование
    log_admin_action(
        db, admin, "create",
        target_type="tournament",
        target_id=tournament.id,
        details=f"Created tournament: {name}",
        request=request
    )

    response = RedirectResponse("/admin/tournaments", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Турнир {name} успешно создан",
        "success"
    ))
    return response


@router.get("/{tournament_id}/edit", response_class=HTMLResponse)
async def admin_tournaments_edit_page(
    request: Request,
    tournament_id: int,
    db: Session = Depends(get_db)
):
    """Страница редактирования турнира"""
    admin = require_admin(request, db)

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Турнир не найден")

    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()

    csrf_token = generate_csrf_token()
    return templates.TemplateResponse("admin/tournaments_form.html", {
        "request": request,
        "admin": admin,
        "disciplines": disciplines,
        "tournament": tournament,
        "action": "edit",
        "csrf_token": csrf_token
    })


@router.post("/{tournament_id}/update")
async def admin_tournaments_update(
    request: Request,
    tournament_id: int,
    name: str = Form(...),
    discipline_id: int = Form(...),
    description: str = Form(""),
    prize_pool: str = Form(""),
    max_teams: int = Form(16),
    registration_deadline_str: str = Form(""),
    start_date_str: str = Form(""),
    end_date_str: str = Form(""),
    status: str = Form("upcoming"),
    format: str = Form("single_elimination"),
    is_online: bool = Form(False),
    image_url: str = Form(""),
    db: Session = Depends(get_db)
):
    """Обновление турнира"""
    admin = require_admin(request, db)

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Турнир не найден")

    # Парсинг дат
    registration_deadline = None
    start_date = None
    end_date = None

    if registration_deadline_str:
        try:
            registration_deadline = datetime.strptime(registration_deadline_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            pass

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            pass

    # Валидация дат
    if registration_deadline and start_date and registration_deadline >= start_date:
        disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
        csrf_token = generate_csrf_token()
        return templates.TemplateResponse("admin/tournaments_form.html", {
            "request": request,
            "admin": admin,
            "disciplines": disciplines,
            "tournament": tournament,
            "action": "edit",
            "error": "Регистрация должна завершиться до начала турнира",
            "csrf_token": csrf_token
        })

    if start_date and end_date and start_date >= end_date:
        disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
        csrf_token = generate_csrf_token()
        return templates.TemplateResponse("admin/tournaments_form.html", {
            "request": request,
            "admin": admin,
            "disciplines": disciplines,
            "tournament": tournament,
            "action": "edit",
            "error": "Дата начала должна быть раньше даты окончания",
            "csrf_token": csrf_token
        })

    # Сохранение изменений
    old_status = tournament.status

    tournament.name = name
    tournament.discipline_id = discipline_id
    tournament.description = description
    tournament.prize_pool = prize_pool
    tournament.max_teams = max_teams
    tournament.registration_deadline = registration_deadline
    tournament.start_date = start_date
    tournament.end_date = end_date
    tournament.status = status
    tournament.format = format
    tournament.is_online = is_online
    tournament.image_url = image_url

    db.commit()

    # Логирование
    log_admin_action(
        db, admin, "update",
        target_type="tournament",
        target_id=tournament.id,
        details=f"Updated tournament: {name} (status: {old_status}->{status})",
        request=request
    )

    response = RedirectResponse("/admin/tournaments", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Турнир {name} успешно обновлён",
        "success"
    ))
    return response


@router.post("/{tournament_id}/delete")
async def admin_tournaments_delete(
    request: Request,
    tournament_id: int,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    """Удаление турнира"""
    admin = require_admin(request, db)

    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Турнир не найден")

    tournament_name = tournament.name
    db.delete(tournament)
    db.commit()

    # Логирование
    log_admin_action(
        db, admin, "delete",
        target_type="tournament",
        target_id=tournament_id,
        details=f"Deleted tournament: {tournament_name}",
        request=request
    )

    response = RedirectResponse("/admin/tournaments", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Турнир {tournament_name} удалён",
        "success"
    ))
    return response


# ==================== Управление заявками команд ====================

@router.get("/{tournament_id}/participations", response_class=HTMLResponse)
async def admin_tournament_participations(
    request: Request,
    tournament_id: int,
    db: Session = Depends(get_db)
):
    """Страница управления заявками команд на турнир"""
    admin = require_admin(request, db)

    tournament = db.query(Tournament).options(
        joinedload(Tournament.discipline)
    ).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Турнир не найден")

    # Получаем все заявки (и подтверждённые, и ожидающие) с загрузкой команд
    participations = db.query(TournamentParticipation).options(
        joinedload(TournamentParticipation.team).joinedload(Team.discipline),
        joinedload(TournamentParticipation.team).joinedload(Team.captain)
    ).filter(
        TournamentParticipation.tournament_id == tournament_id
    ).order_by(TournamentParticipation.registered_at.desc()).all()

    flash_data = None
    flash_cookie = request.cookies.get("flash_message")
    if flash_cookie:
        from utils import parse_flash_message
        flash_data = parse_flash_message(flash_cookie)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("admin/tournament_participations.html", {
        "request": request,
        "admin": admin,
        "tournament": tournament,
        "participations": participations,
        "flash": flash_data,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    if flash_cookie:
        response.delete_cookie("flash_message")
    return response


@router.post("/{tournament_id}/participations/{participation_id}/confirm")
async def admin_confirm_participation(
    request: Request,
    tournament_id: int,
    participation_id: int,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    """Подтверждение участия команды в турнире"""
    admin = require_admin(request, db)

    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    participation = db.query(TournamentParticipation).filter(
        TournamentParticipation.id == participation_id,
        TournamentParticipation.tournament_id == tournament_id
    ).first()
    if not participation:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    participation.is_confirmed = True
    db.commit()

    team_name = participation.team.name if participation.team else "Unknown"
    
    # Отправка email уведомления
    if participation.team and participation.team.captain:
        captain = participation.team.captain
        start_date_str = tournament.start_date.strftime('%d.%m.%Y %H:%M') if tournament.start_date else "будет объявлена"
        try:
            await send_tournament_confirmation_email(
                email=captain.email,
                username=captain.username,
                team_name=team_name,
                tournament_name=tournament.name,
                start_date=start_date_str
            )
        except Exception as e:
            print(f"Email not sent: {e}")

    log_admin_action(
        db, admin, "confirm",
        target_type="participation",
        target_id=participation_id,
        details=f"Confirmed team {team_name} for tournament",
        request=request
    )

    response = RedirectResponse(f"/admin/tournaments/{tournament_id}/participations", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Команда {team_name} подтверждена для участия в турнире",
        "success"
    ))
    return response


@router.post("/{tournament_id}/participations/{participation_id}/reject")
async def admin_reject_participation(
    request: Request,
    tournament_id: int,
    participation_id: int,
    csrf_token: str = Form(None),
    reason: str = Form(None),
    db: Session = Depends(get_db)
):
    """Отказ команде в участии в турнире"""
    admin = require_admin(request, db)

    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    participation = db.query(TournamentParticipation).filter(
        TournamentParticipation.id == participation_id,
        TournamentParticipation.tournament_id == tournament_id
    ).first()
    if not participation:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    team_name = participation.team.name if participation.team else "Unknown"
    
    # Отправка email уведомления об отказе
    if participation.team and participation.team.captain:
        captain = participation.team.captain
        try:
            await send_tournament_rejection_email(
                email=captain.email,
                username=captain.username,
                team_name=team_name,
                tournament_name=tournament.name,
                reason=reason or ""
            )
        except Exception as e:
            print(f"Email not sent: {e}")
    
    db.delete(participation)
    db.commit()

    log_admin_action(
        db, admin, "reject",
        target_type="participation",
        target_id=participation_id,
        details=f"Rejected team {team_name} for tournament",
        request=request
    )

    response = RedirectResponse(f"/admin/tournaments/{tournament_id}/participations", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Команде {team_name} отказано в участии",
        "info"
    ))
    return response


@router.post("/{tournament_id}/participations/{participation_id}/delete")
async def admin_delete_participation(
    request: Request,
    tournament_id: int,
    participation_id: int,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    """Удаление заявки команды из турнира"""
    admin = require_admin(request, db)

    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    participation = db.query(TournamentParticipation).filter(
        TournamentParticipation.id == participation_id,
        TournamentParticipation.tournament_id == tournament_id
    ).first()
    if not participation:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    team_name = participation.team.name if participation.team else "Unknown"

    db.delete(participation)
    db.commit()

    log_admin_action(
        db, admin, "delete",
        target_type="participation",
        target_id=participation_id,
        details=f"Deleted team {team_name} from tournament",
        request=request
    )

    response = RedirectResponse(f"/admin/tournaments/{tournament_id}/participations", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Команда {team_name} удалена из турнира",
        "info"
    ))
    return response
