from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from models import User, get_db, TournamentParticipation, Tournament
from schemas import UserRegister, UserLogin, VerifyEmail
from utils import get_password_hash, verify_password, create_verification_token, create_access_token
from mailer import send_verification_email
from datetime import timedelta
from config import settings
from jose import jwt, JWTError
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Валидация email regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Получить текущего пользователя из cookie"""
    token = request.cookies.get("access_token")
    if not token:
        return None

    # Удаляем кавычки если они есть
    token = token.strip('"')
    
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


def require_auth(request: Request, db: Session = Depends(get_db)):
    """Требовать аутентификацию"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=403, detail="Требуется авторизация")
    return user


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Валидация email
    if not EMAIL_REGEX.match(email):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Некорректный формат email"
        })

    # Валидация username
    if len(username) < 3 or len(username) > 50:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Имя пользователя должно быть от 3 до 50 символов"
        })

    # Валидация пароля
    if len(password) < 6:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Пароль должен содержать минимум 6 символов"
        })

    email = email.lower().strip()
    username = username.strip()

    # Проверка на существующего пользователя с безопасным сообщением
    existing_user = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()

    if existing_user:
        # Не раскрываем, какое именно поле занято
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Пользователь с такими данными уже существует"
        })

    verification_token = create_verification_token(email)

    new_user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        verification_token=verification_token,
        is_verified=True,  # Авто-верификация для локальной разработки
        is_active=True
    )

    db.add(new_user)
    db.commit()

    logger.info(f"New user registered: {username} ({email})")

    # Отправка email (не критично если ошибка)
    try:
        if settings.mail_username and settings.mail_password:
            await send_verification_email(email, username, verification_token)
    except Exception as e:
        logger.warning(f"Email not sent to {email}: {e}")

    return templates.TemplateResponse("register.html", {
        "request": request,
        "success": f"Пользователь {username} успешно зарегистрирован! Теперь вы можете войти."
    })


@router.get("/verify", response_class=HTMLResponse)
async def verify_email_page(request: Request, token: str = None):
    if not token:
        return templates.TemplateResponse("verify.html", {
            "request": request,
            "error": "Токен не предоставлен"
        })

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        token_type = payload.get("type")

        if token_type != "verification":
            raise HTTPException(status_code=400, detail="Неверный тип токена")

        db = next(get_db())
        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        if user.is_verified:
            return templates.TemplateResponse("verify.html", {
                "request": request,
                "message": "Email уже подтверждён"
            })

        user.is_verified = True
        user.is_active = True
        user.verification_token = None
        db.commit()

        return templates.TemplateResponse("verify.html", {
            "request": request,
            "message": "Email успешно подтверждён! Теперь вы можете войти."
        })

    except JWTError:
        return templates.TemplateResponse("verify.html", {
            "request": request,
            "error": "Неверный или истёкший токен"
        })


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Неверный email или пароль"
        })

    if not user.is_verified:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Подтвердите email перед входом"
        })

    access_token = create_access_token(
        data={"sub": user.email, "type": "access"},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    # Редирект на /dashboard вместо рендеринга шаблона
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,  # 30 минут
        path="/",
        domain="localhost",
        samesite="lax"
    )
    return response


@router.get("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """Выход пользователя с удалением cookie"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token", path="/", domain="localhost")
    return response


# ==================== Восстановление пароля ====================

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Страница запроса восстановления пароля"""
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """Запрос на восстановление пароля"""
    user = db.query(User).filter(User.email == email.lower().strip()).first()

    # Всегда показываем успех (не раскрываем наличие email)
    success_message = (
        "Если аккаунт с таким email существует, "
        "вы получите инструкцию по сбросу пароля."
    )

    if user and user.is_verified:
        # Создаём токен сброса
        from models import PasswordResetToken
        from utils import create_reset_token
        from datetime import datetime, timedelta
        from mailer import send_password_reset_email

        token = create_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.add(reset_token)
        db.commit()

        logger.info(f"Password reset requested for: {email}")

        # Отправляем email (не критично если ошибка)
        try:
            if settings.mail_username and settings.mail_password:
                await send_password_reset_email(email, user.username, token)
        except Exception as e:
            logger.warning(f"Password reset email not sent to {email}: {e}")

    return templates.TemplateResponse("forgot_password.html", {
        "request": request,
        "success": success_message
    })


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = None):
    """Страница сброса пароля"""
    if not token:
        return templates.TemplateResponse("reset_password.html", {
            "request": request,
            "error": "Токен не предоставлен"
        })

    # Проверяем токен
    from models import PasswordResetToken
    from datetime import datetime

    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()

    if not reset_token:
        return templates.TemplateResponse("reset_password.html", {
            "request": request,
            "error": "Неверный или истёкший токен"
        })

    return templates.TemplateResponse("reset_password.html", {
        "request": request,
        "token": token
    })


@router.post("/reset-password")
async def reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Сброс пароля"""
    from models import PasswordResetToken
    from datetime import datetime
    from utils import get_password_hash

    # Проверка пароля
    if len(new_password) < 6:
        return templates.TemplateResponse("reset_password.html", {
            "request": request,
            "token": token,
            "error": "Пароль должен содержать минимум 6 символов"
        })

    # Проверяем токен
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()

    if not reset_token:
        return templates.TemplateResponse("reset_password.html", {
            "request": request,
            "error": "Неверный или истёкший токен"
        })

    # Обновляем пароль
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if user:
        user.hashed_password = get_password_hash(new_password)
        reset_token.is_used = True
        db.commit()
        logger.info(f"Password reset successful for: {user.email}")

    return templates.TemplateResponse("reset_password.html", {
        "request": request,
        "success": "Пароль успешно изменён! Теперь вы можете войти."
    })


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})
