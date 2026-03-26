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

router = APIRouter()
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
    user = db.query(User).filter((User.email == email) | (User.username == username)).first()

    if user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Пользователь с таким email или именем уже существует"
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

    # Отправка email (не критично если ошибка)
    try:
        if settings.mail_username and settings.mail_password:
            await send_verification_email(email, username, verification_token)
    except Exception as e:
        print(f"Email not sent: {e}")

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

    response = templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user
    })
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Личный кабинет - требует аутентификации"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user
    })


@router.get("/my-tournaments")
async def my_tournaments(request: Request, db: Session = Depends(get_db)):
    """Страница 'Мои турниры' - турниры где участвует пользователь"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    # Получаем команды пользователя
    from models import Team
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


@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})
