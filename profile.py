"""
Личный кабинет пользователя
Профиль, настройки, команды, история турниров
"""

import os
import uuid
import logging
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from models import get_db, User, Team, Discipline, TournamentParticipation, Tournament, user_disciplines
from auth import get_current_user_from_cookie
from utils import get_password_hash, verify_password, generate_csrf_token, validate_csrf_token, create_flash_message
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["profile"])
templates = Jinja2Templates(directory="templates")

BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Личный кабинет - главная страница"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=str(request.url_for('login_page')), status_code=303)

    # Получаем команды пользователя
    user_teams = db.query(Team).filter(Team.captain_id == user.id).all()
    
    # Получаем последние участия в турнирах
    participations = db.query(TournamentParticipation).options(
        joinedload(TournamentParticipation.tournament).joinedload(Tournament.discipline),
        joinedload(TournamentParticipation.team)
    ).filter(
        TournamentParticipation.user_id == user.id
    ).order_by(TournamentParticipation.registered_at.desc()).limit(5).all()

    # Статистика
    stats = {
        "total_teams": len(user_teams),
        "total_tournaments": len(participations),
        "total_matches": user.total_matches,
        "win_rate": (user.total_wins / user.total_matches * 100) if user.total_matches > 0 else 0
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "teams": user_teams,
        "recent_participations": participations,
        "stats": stats
    })


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    """Страница профиля пользователя"""
    try:
        user = get_current_user_from_cookie(request, db)
        if not user:
            return RedirectResponse(url=str(request.url_for('login_page')), status_code=303)

        logger.info(f"Profile page for user: {user.username}")
        
        # Получаем все дисциплины
        disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
        
        # Получаем выбранные дисциплины пользователя
        user_discipline_ids = [d.id for d in user.disciplines]
        
        csrf_token = generate_csrf_token()
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user,
            "disciplines": disciplines,
            "user_discipline_ids": user_discipline_ids,
            "csrf_token": csrf_token
        })
    except Exception as e:
        logger.error(f"Profile page error: {e}", exc_info=True)
        raise


@router.post("/profile/update")
async def update_profile(
    request: Request,
    username: str = Form(...),
    bio: str = Form(""),
    country: str = Form(""),
    city: str = Form(""),
    social_vk: str = Form(""),
    social_telegram: str = Form(""),
    social_discord: str = Form(""),
    discipline_ids: str = Form(None),
    db: Session = Depends(get_db)
):
    """Обновление профиля пользователя"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=str(request.url_for('login_page')), status_code=303)

    # Проверка username
    if len(username) < 3 or len(username) > 50:
        response = RedirectResponse("/profile", status_code=303)
        response.set_cookie("flash_message", create_flash_message(
            "Имя пользователя должно быть от 3 до 50 символов", "error"
        ))
        return response

    # Проверка уникальности username
    existing = db.query(User).filter(User.username == username, User.id != user.id).first()
    if existing:
        response = RedirectResponse("/profile", status_code=303)
        response.set_cookie("flash_message", create_flash_message(
            "Это имя пользователя уже занято", "error"
        ))
        return response

    # Обновление
    user.username = username
    user.bio = bio or None
    user.country = country or None
    user.city = city or None
    user.social_vk = social_vk or None
    user.social_telegram = social_telegram or None
    user.social_discord = social_discord or None

    # Обновление дисциплин
    if discipline_ids:
        # Преобразуем строку в список (FastAPI Form возвращает строку для list)
        import re
        ids = re.findall(r'\d+', discipline_ids) if discipline_ids else []
        
        if ids:
            # Получаем дисциплины
            selected_disciplines = db.query(Discipline).filter(
                Discipline.id.in_([int(i) for i in ids]),
                Discipline.is_active == True
            ).all()
            
            # Очищаем текущие связи и добавляем новые
            user.disciplines = selected_disciplines

    db.commit()
    logger.info(f"Profile updated for user {user.username}")

    response = RedirectResponse("/profile", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        "Профиль успешно обновлён", "success"
    ))
    return response


@router.post("/profile/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Загрузка аватара пользователя"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return JSONResponse(status_code=403, content={"error": "Требуется авторизация"})

    try:
        # Проверка размера файла (макс 5MB)
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > settings.max_upload_size_bytes:
            return JSONResponse(
                status_code=400,
                content={"error": f"Файл слишком большой. Максимум {settings.max_upload_size_mb}MB"}
            )

        # Проверка расширения
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return JSONResponse(
                status_code=400,
                content={"error": f"Недопустимый формат. Разрешены: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"}
            )

        # Проверка MIME типа
        if not file.content_type.startswith('image/'):
            return JSONResponse(
                status_code=400,
                content={"error": "Файл не является изображением"}
            )

        # Сохранение
        unique_filename = f"avatar_{user.id}_{uuid.uuid4().hex}{ext}"
        file_path = UPLOAD_DIR / unique_filename

        with open(file_path, "wb") as f:
            f.write(contents)

        # Удаляем старый аватар если есть
        if user.avatar_url:
            old_path = BASE_DIR / "static" / user.avatar_url.lstrip("/")
            if os.path.exists(old_path):
                os.remove(old_path)

        user.avatar_url = f"/static/uploads/avatars/{unique_filename}"
        db.commit()

        logger.info(f"Avatar uploaded for user {user.username}")
        return JSONResponse(content={"location": user.avatar_url})

    except Exception as e:
        logger.error(f"Avatar upload error: {e}")
        return JSONResponse(status_code=500, content={"error": f"Ошибка загрузки: {str(e)}"})


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    """Страница настроек аккаунта"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=str(request.url_for('login_page')), status_code=303)

    csrf_token = generate_csrf_token()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user,
        "csrf_token": csrf_token
    })


@router.post("/settings/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Смена пароля"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=str(request.url_for('login_page')), status_code=303)

    # Проверка текущего пароля
    if not verify_password(current_password, user.hashed_password):
        response = RedirectResponse("/settings", status_code=303)
        response.set_cookie("flash_message", create_flash_message(
            "Текущий пароль указан неверно", "error"
        ))
        return response

    # Проверка нового пароля
    if len(new_password) < 6:
        response = RedirectResponse("/settings", status_code=303)
        response.set_cookie("flash_message", create_flash_message(
            "Пароль должен содержать минимум 6 символов", "error"
        ))
        return response

    # Проверка совпадения паролей
    if new_password != confirm_password:
        response = RedirectResponse("/settings", status_code=303)
        response.set_cookie("flash_message", create_flash_message(
            "Новые пароли не совпадают", "error"
        ))
        return response

    # Обновление пароля
    user.hashed_password = get_password_hash(new_password)
    db.commit()

    logger.info(f"Password changed for user {user.username}")

    response = RedirectResponse("/settings", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        "Пароль успешно изменён", "success"
    ))
    return response


@router.post("/settings/notifications")
async def update_notifications(
    request: Request,
    notify_email_tournaments: str = Form(None),
    notify_email_news: str = Form(None),
    db: Session = Depends(get_db)
):
    """Обновление настроек уведомлений"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=str(request.url_for('login_page')), status_code=303)

    user.notify_email_tournaments = (notify_email_tournaments == "on")
    user.notify_email_news = (notify_email_news == "on")

    db.commit()
    logger.info(f"Notification settings updated for user {user.username}")

    response = RedirectResponse("/settings", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        "Настройки уведомлений обновлены", "success"
    ))
    return response


@router.post("/settings/privacy")
async def update_privacy(
    request: Request,
    is_profile_public: str = Form(None),
    db: Session = Depends(get_db)
):
    """Обновление настроек приватности"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=str(request.url_for('login_page')), status_code=303)

    user.is_profile_public = (is_profile_public == "on")

    db.commit()
    logger.info(f"Privacy settings updated for user {user.username}")

    response = RedirectResponse("/settings", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        "Настройки приватности обновлены", "success"
    ))
    return response


@router.get("/my-teams", response_class=HTMLResponse)
async def my_teams_page(request: Request, db: Session = Depends(get_db)):
    """Страница моих команд"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=str(request.url_for('login_page')), status_code=303)

    # Команды где пользователь капитан
    captain_teams = db.query(Team).options(
        joinedload(Team.discipline)
    ).filter(Team.captain_id == user.id).all()

    return templates.TemplateResponse("my_teams.html", {
        "request": request,
        "user": user,
        "teams": captain_teams
    })


@router.get("/create-team", response_class=HTMLResponse)
async def create_team_page(request: Request, db: Session = Depends(get_db)):
    """Страница создания команды"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=str(request.url_for('login_page')), status_code=303)

    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
    csrf_token = generate_csrf_token()

    return templates.TemplateResponse("create_team.html", {
        "request": request,
        "user": user,
        "disciplines": disciplines,
        "csrf_token": csrf_token
    })


@router.post("/create-team")
async def create_team(
    request: Request,
    name: str = Form(...),
    discipline_id: int = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    """Создание команды"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=str(request.url_for('login_page')), status_code=303)

    # Проверка названия
    if len(name) < 3 or len(name) > 100:
        response = RedirectResponse("/create-team", status_code=303)
        response.set_cookie("flash_message", create_flash_message(
            "Название команды должно быть от 3 до 100 символов", "error"
        ))
        return response

    # Проверка уникальности
    existing = db.query(Team).filter(Team.name == name).first()
    if existing:
        response = RedirectResponse("/create-team", status_code=303)
        response.set_cookie("flash_message", create_flash_message(
            "Команда с таким названием уже существует", "error"
        ))
        return response

    # Создание
    team = Team(
        name=name,
        discipline_id=discipline_id,
        captain_id=user.id,
        description=description or None,
        rating=1000,
        is_active=True
    )

    db.add(team)
    db.commit()
    db.refresh(team)

    logger.info(f"Team created: {name} by user {user.username}")

    response = RedirectResponse("/my-teams", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Команда {name} успешно создана", "success"
    ))
    return response


@router.get("/my-tournaments", response_class=HTMLResponse)
async def my_tournaments_page(request: Request, db: Session = Depends(get_db)):
    """Страница моих турниров"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=str(request.url_for('login_page')), status_code=303)

    # Получаем команды пользователя
    user_teams = db.query(Team).filter(Team.captain_id == user.id).all()
    user_teams_ids = [t.id for t in user_teams]

    # Получаем заявки на турниры
    participations = db.query(TournamentParticipation).options(
        joinedload(TournamentParticipation.tournament).joinedload(Tournament.discipline),
        joinedload(TournamentParticipation.team)
    ).filter(
        TournamentParticipation.team_id.in_(user_teams_ids) if user_teams_ids else False
    ).order_by(TournamentParticipation.registered_at.desc()).all()

    return templates.TemplateResponse("my_tournaments.html", {
        "request": request,
        "user": user,
        "participations": participations
    })
