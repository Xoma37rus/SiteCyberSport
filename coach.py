from fastapi import APIRouter, Request, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from models import User, CoachStudent, TrainingSession, TrainingAttendance, Discipline, get_db, AdminLog
from utils import generate_csrf_token, validate_csrf_token, create_flash_message
from auth import get_current_user_from_cookie
from datetime import datetime, timedelta
import logging
import os
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coach", tags=["coach"])
templates = Jinja2Templates(directory="templates")


def require_coach(request: Request, db: Session = Depends(get_db)):
    """Требовать права тренера"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=403, detail="Требуется авторизация")
    if user.role != "trainer":
        raise HTTPException(status_code=403, detail="Требуется роль тренера")
    return user


@router.get("/dashboard", response_class=HTMLResponse)
async def coach_dashboard(request: Request, db: Session = Depends(get_db)):
    """Главная страница тренера"""
    coach = require_coach(request, db)

    # Получаем всех учеников тренера
    students_rel = db.query(CoachStudent).filter(CoachStudent.coach_id == coach.id).all()
    students = [rel.student for rel in students_rel]

    # Получаем предстоящие тренировки
    upcoming_sessions = db.query(TrainingSession).filter(
        TrainingSession.coach_id == coach.id,
        TrainingSession.status == "scheduled",
        TrainingSession.scheduled_at >= datetime.utcnow()
    ).order_by(TrainingSession.scheduled_at).limit(5).all()

    # Статистика
    total_students = len(students)
    total_sessions = db.query(TrainingSession).filter(
        TrainingSession.coach_id == coach.id
    ).count()
    completed_sessions = db.query(TrainingSession).filter(
        TrainingSession.coach_id == coach.id,
        TrainingSession.status == "completed"
    ).count()

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("coach/dashboard.html", {
        "request": request,
        "coach": coach,
        "students": students,
        "upcoming_sessions": upcoming_sessions,
        "stats": {
            "total_students": total_students,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions
        },
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    return response


@router.get("/students", response_class=HTMLResponse)
async def coach_students(request: Request, db: Session = Depends(get_db)):
    """Список учеников тренера"""
    coach = require_coach(request, db)

    students_rel = db.query(CoachStudent).filter(
        CoachStudent.coach_id == coach.id
    ).options(joinedload(CoachStudent.student)).all()

    students = []
    for rel in students_rel:
        students.append({
            "student": rel.student,
            "notes": rel.notes,
            "created_at": rel.created_at,
            "relation_id": rel.id
        })

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("coach/students.html", {
        "request": request,
        "coach": coach,
        "students": students,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    return response


@router.get("/students/add", response_class=HTMLResponse)
async def add_student_page(request: Request, db: Session = Depends(get_db)):
    """Страница добавления ученика"""
    coach = require_coach(request, db)

    # Получаем всех пользователей с ролью student для выбора
    available_students = db.query(User).filter(
        User.role.in_(["student", "student_pro", "student_ult", "user"])
    ).order_by(User.username).all()

    # Получаем уже добавленных учеников
    existing_student_ids = db.query(CoachStudent.student_id).filter(
        CoachStudent.coach_id == coach.id
    ).all()
    existing_student_ids = [s[0] for s in existing_student_ids]

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("coach/add_student.html", {
        "request": request,
        "coach": coach,
        "available_students": available_students,
        "existing_student_ids": existing_student_ids,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    return response


@router.post("/students/add")
async def add_student(
    request: Request,
    db: Session = Depends(get_db)
):
    """Добавление ученика"""
    coach = require_coach(request, db)

    form = await request.form()
    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(form.get("csrf_token"), session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    student_id = int(form.get("student_id"))
    notes = form.get("notes", "")

    # Проверяем существование ученика
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    # Проверяем, нет ли уже такой связи
    existing = db.query(CoachStudent).filter(
        CoachStudent.coach_id == coach.id,
        CoachStudent.student_id == student_id
    ).first()

    if existing:
        response = RedirectResponse("/coach/students/add", status_code=303)
        response.set_cookie("flash_message", create_flash_message(
            f"{student.username} уже является вашим учеником",
            "error"
        ))
        return response

    # Создаём связь
    relation = CoachStudent(
        coach_id=coach.id,
        student_id=student_id,
        notes=notes
    )
    db.add(relation)
    db.commit()

    response = RedirectResponse("/coach/students", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"{student.username} добавлен в ваши ученики",
        "success"
    ))
    return response


@router.post("/students/{student_id}/remove")
async def remove_student(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Удаление ученика из списка"""
    coach = require_coach(request, db)

    form = await request.form()
    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(form.get("csrf_token"), session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    relation = db.query(CoachStudent).filter(
        CoachStudent.coach_id == coach.id,
        CoachStudent.student_id == student_id
    ).first()

    if not relation:
        raise HTTPException(status_code=404, detail="Связь не найдена")

    student = db.query(User).filter(User.id == student_id).first()
    db.delete(relation)
    db.commit()

    response = RedirectResponse("/coach/students", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"{student.username} удалён из ваших учеников",
        "success"
    ))
    return response


@router.get("/students/{student_id}", response_class=HTMLResponse)
async def student_detail(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Страница ученика с подробной информацией"""
    coach = require_coach(request, db)

    # Проверяем, что ученик принадлежит тренеру
    relation = db.query(CoachStudent).filter(
        CoachStudent.coach_id == coach.id,
        CoachStudent.student_id == student_id
    ).first()

    if not relation:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    student = relation.student

    # Получаем тренировки с участием ученика
    student_sessions = db.query(TrainingSession).join(
        TrainingAttendance, TrainingSession.id == TrainingAttendance.session_id
    ).filter(
        TrainingSession.coach_id == coach.id,
        TrainingAttendance.student_id == student_id
    ).order_by(TrainingSession.scheduled_at.desc()).limit(10).all()

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("coach/student_detail.html", {
        "request": request,
        "coach": coach,
        "student": student,
        "notes": relation.notes,
        "sessions": student_sessions,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    return response


@router.post("/students/{student_id}/update-notes")
async def update_student_notes(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Обновление заметок об ученике"""
    coach = require_coach(request, db)

    form = await request.form()
    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(form.get("csrf_token"), session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    relation = db.query(CoachStudent).filter(
        CoachStudent.coach_id == coach.id,
        CoachStudent.student_id == student_id
    ).first()

    if not relation:
        raise HTTPException(status_code=404, detail="Связь не найдена")

    relation.notes = form.get("notes", "")
    db.commit()

    response = RedirectResponse(f"/coach/students/{student_id}", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        "Заметки обновлены",
        "success"
    ))
    return response


@router.get("/sessions", response_class=HTMLResponse)
async def coach_sessions(request: Request, db: Session = Depends(get_db)):
    """Список тренировок тренера"""
    coach = require_coach(request, db)

    sessions = db.query(TrainingSession).filter(
        TrainingSession.coach_id == coach.id
    ).order_by(TrainingSession.scheduled_at.desc()).all()

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("coach/sessions.html", {
        "request": request,
        "coach": coach,
        "sessions": sessions,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    return response


@router.get("/sessions/create", response_class=HTMLResponse)
async def create_session_page(request: Request, db: Session = Depends(get_db)):
    """Страница создания тренировки"""
    coach = require_coach(request, db)

    # Получаем учеников тренера
    students_rel = db.query(CoachStudent).filter(CoachStudent.coach_id == coach.id).all()
    students = [rel.student for rel in students_rel]

    # Получаем дисциплины
    disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("coach/create_session.html", {
        "request": request,
        "coach": coach,
        "students": students,
        "disciplines": disciplines,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    return response


@router.post("/sessions/create")
async def create_session(
    request: Request,
    db: Session = Depends(get_db)
):
    """Создание тренировки"""
    coach = require_coach(request, db)

    form = await request.form()
    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(form.get("csrf_token"), session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    title = form.get("title", "").strip()
    description = form.get("description", "").strip()
    discipline_id = form.get("discipline_id")
    scheduled_at_str = form.get("scheduled_at")
    duration_minutes = int(form.get("duration_minutes", 60))
    student_ids = form.getlist("student_ids")

    if not title:
        response = RedirectResponse("/coach/sessions/create", status_code=303)
        response.set_cookie("flash_message", create_flash_message(
            "Название тренировки обязательно",
            "error"
        ))
        return response

    scheduled_at = None
    if scheduled_at_str:
        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                scheduled_at = datetime.strptime(scheduled_at_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                pass

    # Создаём тренировку
    session = TrainingSession(
        coach_id=coach.id,
        discipline_id=int(discipline_id) if discipline_id else None,
        title=title,
        description=description,
        scheduled_at=scheduled_at,
        duration_minutes=duration_minutes,
        status="scheduled"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Добавляем учеников как участников
    for sid in student_ids:
        if sid:
            attendance = TrainingAttendance(
                session_id=session.id,
                student_id=int(sid),
                status="pending"
            )
            db.add(attendance)

    db.commit()

    response = RedirectResponse("/coach/sessions", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Тренировка '{title}' создана",
        "success"
    ))
    return response


@router.get("/sessions/{session_id}", response_class=HTMLResponse)
async def session_detail(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Детали тренировки"""
    coach = require_coach(request, db)

    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.coach_id == coach.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    # Получаем участников
    attendees = db.query(TrainingAttendance).filter(
        TrainingAttendance.session_id == session_id
    ).all()

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("coach/session_detail.html", {
        "request": request,
        "coach": coach,
        "session": session,
        "attendees": attendees,
        "csrf_token": csrf_token
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    return response


@router.post("/sessions/{session_id}/update-status")
async def update_session_status(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Обновление статуса тренировки"""
    coach = require_coach(request, db)

    form = await request.form()
    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(form.get("csrf_token"), session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    session = db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.coach_id == coach.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    new_status = form.get("status")
    if new_status in ["scheduled", "completed", "cancelled"]:
        session.status = new_status
        db.commit()

    response = RedirectResponse(f"/coach/sessions/{session_id}", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Статус тренировки обновлён на '{new_status}'",
        "success"
    ))
    return response


@router.post("/sessions/{session_id}/attendance/{student_id}")
async def update_attendance(
    session_id: int,
    student_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Обновление посещаемости"""
    coach = require_coach(request, db)

    form = await request.form()
    session_token = request.cookies.get("csrf_token")
    if not validate_csrf_token(form.get("csrf_token"), session_token):
        raise HTTPException(status_code=403, detail="Ошибка безопасности (CSRF)")

    attendance = db.query(TrainingAttendance).filter(
        TrainingAttendance.session_id == session_id,
        TrainingAttendance.student_id == student_id
    ).first()

    if not attendance:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    new_status = form.get("status")
    if new_status in ["pending", "attended", "missed"]:
        attendance.status = new_status
        db.commit()

    response = RedirectResponse(f"/coach/sessions/{session_id}", status_code=303)
    response.set_cookie("flash_message", create_flash_message(
        f"Статус посещаемости обновлён",
        "success"
    ))
    return response
