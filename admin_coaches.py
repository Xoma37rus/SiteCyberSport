from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User, CoachStudent, get_db, AdminLog, Discipline
from utils import (
    generate_csrf_token,
    validate_csrf_token,
    create_flash_message,
    get_password_hash
)
from admin import get_current_admin_user, require_admin, log_admin_action
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/coaches", tags=["admin_coaches"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def coaches_list(
    request: Request,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Список всех тренеров"""
    admin = require_admin(request, db)

    query = db.query(User).filter(User.role == "trainer")
    total = query.count()
    offset = (page - 1) * limit
    coaches = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    # Подсчитываем количество учеников у каждого тренера
    coaches_with_students = []
    for coach in coaches:
        student_count = db.query(CoachStudent).filter(CoachStudent.coach_id == coach.id).count()
        coaches_with_students.append({
            "coach": coach,
            "student_count": student_count
        })

    flash_data = None
    flash_cookie = request.cookies.get("flash_message")
    if flash_cookie:
        from utils import parse_flash_message
        flash_data = parse_flash_message(flash_cookie)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("admin/coaches_list.html", {
        "request": request,
        "admin": admin,
        "coaches": coaches_with_students,
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
async def create_coach_page(request: Request, db: Session = Depends(get_db)):
    """Страница создания нового тренера"""
    admin = require_admin(request, db)

    flash_data = None
    flash_cookie = request.cookies.get("flash_message")
    if flash_cookie:
        from utils import parse_flash_message
        flash_data = parse_flash_message(flash_cookie)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("admin/create_coach.html", {
        "request": request,
        "admin": admin,
        "flash": flash_data,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    if flash_cookie:
        response.delete_cookie("flash_message")
    return response


@router.post("/create")
async def create_coach(
    request: Request,
    db: Session = Depends(get_db)
):
    """Создание нового тренера"""
    admin = require_admin(request, db)

    form = await request.form()
    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(form.get("csrf_token"), session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    email = form.get("email", "").strip().lower()
    username = form.get("username", "").strip()
    password = form.get("password", "")
    is_active = form.get("is_active") == "true"
    is_verified = form.get("is_verified") == "true"

    # Проверка на существующего пользователя
    existing = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()

    if existing:
        if existing.email == email:
            error = "Пользователь с таким email уже существует"
        else:
            error = "Пользователь с таким именем уже существует"

        response = RedirectResponse("/admin/coaches/create", status_code=303)
        response.set_cookie("flash_message", create_flash_message(error, "error"))
        return response

    # Создание тренера
    new_coach = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        is_active=is_active,
        is_verified=is_verified,
        is_admin=False,
        role="trainer"
    )

    db.add(new_coach)
    db.commit()

    log_admin_action(
        db, admin, "create",
        target_type="coach",
        target_id=new_coach.id,
        details=f"Created coach: {username} ({email})",
        request=request
    )

    response = RedirectResponse("/admin/coaches", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Тренер {username} успешно создан",
        "success"
    ))
    return response


@router.post("/{coach_id}/delete")
async def delete_coach(
    coach_id: int,
    request: Request,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    """Удалить тренера"""
    admin = require_admin(request, db)

    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    coach = db.query(User).filter(User.id == coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Тренер не найден")

    if coach.role != "trainer":
        raise HTTPException(status_code=400, detail="Пользователь не является тренером")

    # Удаляем все связи с учениками
    db.query(CoachStudent).filter(
        (CoachStudent.coach_id == coach_id) | (CoachStudent.student_id == coach_id)
    ).delete()

    username = coach.username
    db.delete(coach)
    db.commit()

    log_admin_action(
        db, admin, "delete",
        target_type="coach",
        target_id=coach_id,
        details=f"Deleted coach: {username}",
        request=request
    )

    response = RedirectResponse("/admin/coaches", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Тренер {username} удалён",
        "success"
    ))
    return response


@router.get("/{coach_id}/students", response_class=HTMLResponse)
async def coach_students(
    coach_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Список учеников тренера"""
    admin = require_admin(request, db)

    coach = db.query(User).filter(User.id == coach_id, User.role == "trainer").first()
    if not coach:
        raise HTTPException(status_code=404, detail="Тренер не найден")

    participations = db.query(CoachStudent).filter(CoachStudent.coach_id == coach_id).all()
    students = []
    for p in participations:
        students.append({
            "student": p.student,
            "notes": p.notes,
            "created_at": p.created_at,
            "participation_id": p.id
        })

    # Получаем всех пользователей для формы добавления
    users = db.query(User).all()

    flash_data = None
    flash_cookie = request.cookies.get("flash_message")
    if flash_cookie:
        from utils import parse_flash_message
        flash_data = parse_flash_message(flash_cookie)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("admin/coach_students.html", {
        "request": request,
        "admin": admin,
        "coach": coach,
        "students": students,
        "users": users,
        "flash": flash_data,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    if flash_cookie:
        response.delete_cookie("flash_message")
    return response


@router.post("/{coach_id}/students/add")
async def add_student_to_coach(
    coach_id: int,
    request: Request,
    student_id: int = Form(...),
    notes: str = Form(None),
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    """Добавить ученика тренеру"""
    admin = require_admin(request, db)

    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    coach = db.query(User).filter(User.id == coach_id, User.role == "trainer").first()
    if not coach:
        raise HTTPException(status_code=404, detail="Тренер не найден")

    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    # Проверяем, нет ли уже такой связи
    existing = db.query(CoachStudent).filter(
        CoachStudent.coach_id == coach_id,
        CoachStudent.student_id == student_id
    ).first()

    if existing:
        response = RedirectResponse(f"/admin/coaches/{coach_id}/students", status_code=303)
        response.set_cookie("flash_message", create_flash_message(
            f"{student.username} уже является учеником {coach.username}",
            "error"
        ))
        return response

    # Создаём связь
    relation = CoachStudent(
        coach_id=coach_id,
        student_id=student_id,
        notes=notes
    )
    db.add(relation)
    db.commit()

    log_admin_action(
        db, admin, "create",
        target_type="coach_student",
        target_id=relation.id,
        details=f"Added student {student.username} to coach {coach.username}",
        request=request
    )

    response = RedirectResponse(f"/admin/coaches/{coach_id}/students", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"{student.username} добавлен в ученики к {coach.username}",
        "success"
    ))
    return response


@router.post("/{coach_id}/students/{student_id}/remove")
async def remove_student_from_coach(
    coach_id: int,
    student_id: int,
    request: Request,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db)
):
    """Удалить ученика из списка тренера"""
    admin = require_admin(request, db)

    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(csrf_token, session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    relation = db.query(CoachStudent).filter(
        CoachStudent.coach_id == coach_id,
        CoachStudent.student_id == student_id
    ).first()

    if not relation:
        raise HTTPException(status_code=404, detail="Связь не найдена")

    student = db.query(User).filter(User.id == student_id).first()
    coach = db.query(User).filter(User.id == coach_id).first()

    db.delete(relation)
    db.commit()

    log_admin_action(
        db, admin, "delete",
        target_type="coach_student",
        target_id=relation.id,
        details=f"Removed student {student.username} from coach {coach.username}",
        request=request
    )

    response = RedirectResponse(f"/admin/coaches/{coach_id}/students", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"{student.username} удалён из учеников",
        "success"
    ))
    return response
