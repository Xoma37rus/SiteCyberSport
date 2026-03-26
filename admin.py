from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User, get_db, AdminLog
from utils import (
    verify_password,
    create_access_token,
    generate_csrf_token,
    validate_csrf_token,
    create_flash_message,
    get_password_hash
)
from datetime import timedelta
from config import settings
from jose import jwt, JWTError
from typing import Optional

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


def get_client_ip(request: Request) -> str:
    """Получение IP адреса клиента"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"


def log_admin_action(db: Session, admin: User, action: str, target_type: str = None,
                     target_id: int = None, details: str = None, request: Request = None):
    """Логирование действия администратора"""
    try:
        log = AdminLog(
            admin_id=admin.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=get_client_ip(request) if request else None
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Log error: {e}")


def get_current_admin_user(request: Request, db: Session = Depends(get_db)):
    """Получить текущего администратора из cookie"""
    token = request.cookies.get("admin_access_token")
    if not token:
        return None

    if token.startswith("Bearer "):
        token = token[7:]

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        if user and user.is_admin and user.is_verified:
            return user
    except JWTError:
        pass
    return None


def require_admin(request: Request, db: Session = Depends(get_db)):
    """Требовать права администратора"""
    user = get_current_admin_user(request, db)
    if not user:
        raise HTTPException(status_code=403, detail="Требуется вход администратора")
    return user


@router.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    """Главная страница админ-панели"""
    admin = get_current_admin_user(request, db)
    if not admin:
        return RedirectResponse("/admin/login", status_code=303)

    users = db.query(User).all()
    stats = {
        "total_users": len(users),
        "verified_users": len([u for u in users if u.is_verified]),
        "active_users": len([u for u in users if u.is_active]),
        "admin_users": len([u for u in users if u.is_admin]),
    }

    flash_data = None
    flash_cookie = request.cookies.get("flash_message")
    if flash_cookie:
        from utils import parse_flash_message
        flash_data = parse_flash_message(flash_cookie)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "admin": admin,
        "users": users,
        "stats": stats,
        "flash": flash_data,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    if flash_cookie:
        response.delete_cookie("flash_message")
    return response


@router.get("/test", response_class=HTMLResponse)
async def admin_test(request: Request):
    """Тестовая страница"""
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "error": "TEST ERROR MESSAGE"
    })


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Страница входа для администратора"""
    flash_data = None
    flash_cookie = request.cookies.get("flash_message")
    if flash_cookie:
        from utils import parse_flash_message
        flash_data = parse_flash_message(flash_cookie)

    csrf_token = generate_csrf_token()
    
    response = templates.TemplateResponse("admin/login.html", {
        "request": request,
        "flash": flash_data,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    if flash_cookie:
        response.delete_cookie("flash_message")
    return response


@router.post("/login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Вход администратора"""
    print(f"LOGIN ATTEMPT: {email}")
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        print(f"User not found: {email}")
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Неверный email или пароль"
        })
    
    print(f"User found: {user.username}, is_admin: {user.is_admin}")
    
    pw_ok = verify_password(password, user.hashed_password)
    print(f"Password check: {pw_ok}")
    
    if not pw_ok:
        log_admin_action(db, user, "login_failed", details=f"Failed login for {email}", request=request)
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Неверный email или пароль"
        })

    if not user.is_admin:
        log_admin_action(db, user, "login_denied", details=f"Non-admin login attempt: {email}", request=request)
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "У вас нет прав администратора"
        })

    if not user.is_verified:
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "error": "Подтвердите email перед входом"
        })

    access_token = create_access_token(
        data={"sub": user.email, "type": "admin_access"},
        expires_delta=timedelta(hours=8)
    )

    log_admin_action(db, user, "login", request=request)
    print(f"Login successful: {email}")

    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie(key="admin_access_token", value=f"Bearer {access_token}", httponly=True)
    return response


@router.get("/logout")
async def admin_logout(request: Request, db: Session = Depends(get_db)):
    """Выход администратора"""
    admin = get_current_admin_user(request, db)
    if admin:
        log_admin_action(db, admin, "logout", request=request)

    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie("admin_access_token")
    return response


@router.get("/logs", response_class=HTMLResponse)
async def admin_logs(
    request: Request,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Просмотр лога действий администратора"""
    admin = require_admin(request, db)

    total = db.query(AdminLog).count()
    offset = (page - 1) * limit
    logs = db.query(AdminLog).order_by(AdminLog.created_at.desc()).offset(offset).limit(limit).all()

    return templates.TemplateResponse("admin/logs.html", {
        "request": request,
        "admin": admin,
        "logs": logs,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    })


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    page: int = 1,
    limit: int = 20,
    search: str = None,
    db: Session = Depends(get_db)
):
    """Список всех пользователей с пагинацией и поиском"""
    admin = require_admin(request, db)

    query = db.query(User)

    if search:
        query = query.filter(
            (User.email.contains(search)) | (User.username.contains(search))
        )

    total = query.count()
    offset = (page - 1) * limit
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    flash_data = None
    flash_cookie = request.cookies.get("flash_message")
    if flash_cookie:
        from utils import parse_flash_message
        flash_data = parse_flash_message(flash_cookie)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("admin/users.html", {
        "request": request,
        "admin": admin,
        "users": users,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit,
        "search_query": search or "",
        "flash": flash_data,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    if flash_cookie:
        response.delete_cookie("flash_message")

    return response


@router.post("/users/{user_id}/toggle-admin")
async def toggle_admin_status(
    user_id: int,
    request: Request,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    """Переключить статус администратора пользователя"""
    admin = require_admin(request, db)

    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Нельзя изменить свои права")

    old_status = user.is_admin
    user.is_admin = not user.is_admin
    db.commit()

    log_admin_action(
        db, admin, "update",
        target_type="user",
        target_id=user.id,
        details=f"Changed admin status: {old_status} -> {user.is_admin}",
        request=request
    )

    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Права администратора для {user.username} {'предоставлены' if user.is_admin else 'сняты'}",
        "success"
    ))
    return response


@router.post("/users/{user_id}/toggle-active")
async def toggle_active_status(
    user_id: int,
    request: Request,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    """Переключить статус активности пользователя"""
    admin = require_admin(request, db)

    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    old_status = user.is_active
    user.is_active = not user.is_active
    db.commit()

    log_admin_action(
        db, admin, "update",
        target_type="user",
        target_id=user.id,
        details=f"Changed active status: {old_status} -> {user.is_active}",
        request=request
    )

    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Пользователь {user.username} {'активирован' if user.is_active else 'деактивирован'}",
        "success"
    ))
    return response


@router.post("/users/{user_id}/delete")
async def delete_user(
    user_id: int,
    request: Request,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    """Удалить пользователя"""
    admin = require_admin(request, db)

    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить себя")

    username = user.username
    db.delete(user)
    db.commit()

    log_admin_action(
        db, admin, "delete",
        target_type="user",
        target_id=user_id,
        details=f"Deleted user: {username}",
        request=request
    )

    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Пользователь {username} удалён",
        "success"
    ))
    return response


@router.get("/users/create", response_class=HTMLResponse)
async def create_user_page(request: Request, db: Session = Depends(get_db)):
    """Страница создания нового пользователя"""
    admin = require_admin(request, db)

    flash_data = None
    flash_cookie = request.cookies.get("flash_message")
    if flash_cookie:
        from utils import parse_flash_message
        flash_data = parse_flash_message(flash_cookie)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("admin/create_user.html", {
        "request": request,
        "admin": admin,
        "flash": flash_data,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    if flash_cookie:
        response.delete_cookie("flash_message")
    return response


@router.post("/users/create")
async def create_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Создание нового пользователя администратором"""
    admin = require_admin(request, db)

    form = await request.form()
    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(form.get("csrf_token"), session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    email = form.get("email", "").strip()
    username = form.get("username", "").strip()
    password = form.get("password", "")
    role = form.get("role", "user")
    is_active = form.get("is_active") == "true"
    is_verified = form.get("is_verified") == "true"
    # is_admin устанавливается автоматически если роль admin
    is_admin = role == "admin"

    # Проверка на существующего пользователя
    existing = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()

    if existing:
        if existing.email == email:
            error = "Пользователь с таким email уже существует"
        else:
            error = "Пользователь с таким именем уже существует"

        response = RedirectResponse("/admin/users/create", status_code=303)
        response.set_cookie("flash_message", create_flash_message(error, "error"))
        return response

    # Создание пользователя
    new_user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        is_active=is_active,
        is_verified=is_verified,
        is_admin=is_admin,
        role=role
    )

    db.add(new_user)
    db.commit()

    log_admin_action(
        db, admin, "create",
        target_type="user",
        target_id=new_user.id,
        details=f"Created user: {username} ({email}), role: {role}",
        request=request
    )

    response = RedirectResponse("/admin/users", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Пользователь {username} успешно создан",
        "success"
    ))
    return response
