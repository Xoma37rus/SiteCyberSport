"""
Student Rating System — рейтинг учеников, изменяемый тренерами и администраторами
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Optional

from models import get_db, User, CoachStudent
from extended_models import StudentRating, StudentRatingChange
from auth import get_current_user_from_cookie
from utils import generate_csrf_token, validate_csrf_token

router = APIRouter(prefix="/student-rating", tags=["student-rating"])
templates = Jinja2Templates(directory="templates")


def require_coach_or_admin(request: Request, db: Session = Depends(get_db)):
    """Требовать права тренера или администратора"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(status_code=403, detail="Требуется авторизация")
    if user.role not in ("trainer", "admin") and not user.is_admin:
        raise HTTPException(status_code=403, detail="Только тренеры и администраторы могут изменять рейтинг")
    return user


def get_or_create_student_rating(db: Session, student_id: int, coach_id: int = None) -> StudentRating:
    """Получить или создать рейтинг ученика"""
    rating = db.query(StudentRating).filter(
        StudentRating.student_id == student_id
    ).first()

    if not rating:
        rating = StudentRating(
            student_id=student_id,
            coach_id=coach_id,
            score=1000,
            grade="N",
        )
        db.add(rating)
        db.flush()

    return rating


# ==================== СТРАНИЦА УЧЕНИКА: просмотр своего рейтинга ====================

@router.get("/my", response_class=HTMLResponse)
async def my_rating_page(request: Request, db: Session = Depends(get_db)):
    """Личная страница рейтинга ученика"""
    student = get_current_user_from_cookie(request, db)
    if not student:
        return RedirectResponse(url="/login?next=/student-rating/my")

    rating = db.query(StudentRating).filter(
        StudentRating.student_id == student.id
    ).first()

    # Если рейтинга нет — создаём
    if not rating:
        rating = get_or_create_student_rating(db, student.id)
        db.commit()
        db.refresh(rating)

    # История изменений
    changes = db.query(StudentRatingChange).filter(
        StudentRatingChange.student_id == student.id
    ).order_by(StudentRatingChange.created_at.desc()).limit(50).all()

    # Тренер
    coach = None
    if rating.coach_id:
        coach = db.query(User).filter(User.id == rating.coach_id).first()

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("student_rating.html", {
        "request": request,
        "current_user": student,
        "rating": rating,
        "changes": changes,
        "coach": coach,
        "csrf_token": csrf_token,
        "is_student_view": True,
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    return response


# ==================== СТРАНИЦА ТРЕНЕРА: управление учениками ====================

@router.get("/coach", response_class=HTMLResponse)
async def coach_rating_page(request: Request, db: Session = Depends(get_db)):
    """Страница тренера: список учеников с рейтингами"""
    coach = get_current_user_from_cookie(request, db)
    if not coach:
        return RedirectResponse(url="/login")
    if coach.role != "trainer" and not coach.is_admin:
        # Обычный пользователь — редирект на свой рейтинг
        return RedirectResponse(url="/student-rating/my")

    # Получаем всех учеников тренера
    coach_students_rel = db.query(CoachStudent).filter(
        CoachStudent.coach_id == coach.id
    ).options(joinedload(CoachStudent.student)).all()

    students_data = []
    for rel in coach_students_rel:
        student = rel.student
        rating = db.query(StudentRating).filter(
            StudentRating.student_id == student.id
        ).first()

        if not rating:
            rating = get_or_create_student_rating(db, student.id, coach.id)
            db.commit()
            db.refresh(rating)

        students_data.append({
            "student": student,
            "rating": rating,
            "notes": rel.notes,
        })

    # Сортировка по рейтингу
    students_data.sort(key=lambda x: x["rating"].score, reverse=True)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("student_rating_coach.html", {
        "request": request,
        "current_user": coach,
        "students_data": students_data,
        "csrf_token": csrf_token,
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    return response


# ==================== СТРАНИЦА АДМИНА: все ученики ====================

@router.get("/admin", response_class=HTMLResponse)
async def admin_rating_page(request: Request, db: Session = Depends(get_db)):
    """Админ-панель: все ученики с рейтингами"""
    admin = get_current_user_from_cookie(request, db)
    if not admin or not admin.is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    # Все ученики (пользователи с ролью student*)
    students = db.query(User).filter(
        User.role.like("student%")
    ).order_by(User.username).all()

    students_data = []
    for student in students:
        rating = db.query(StudentRating).filter(
            StudentRating.student_id == student.id
        ).first()

        if not rating:
            rating = get_or_create_student_rating(db, student.id)
            db.commit()
            db.refresh(rating)

        coach = None
        if rating.coach_id:
            coach = db.query(User).filter(User.id == rating.coach_id).first()

        students_data.append({
            "student": student,
            "rating": rating,
            "coach": coach,
        })

    students_data.sort(key=lambda x: x["rating"].score, reverse=True)

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("student_rating_admin.html", {
        "request": request,
        "current_user": admin,
        "students_data": students_data,
        "csrf_token": csrf_token,
    })
    response.set_cookie("csrf_token", csrf_token, httponly=True, max_age=3600)
    return response


# ==================== API: Изменение рейтинга ====================

@router.post("/api/change")
async def change_student_rating(
    request: Request,
    student_id: int = Form(...),
    score_change: int = Form(...),
    reason: Optional[str] = Form(None),
    behavior_change: Optional[int] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Изменить рейтинг ученика (тренер/админ)"""
    changer = get_current_user_from_cookie(request, db)
    if not changer:
        return JSONResponse({"error": "Требуется авторизация"}, status_code=401)
    if changer.role != "trainer" and not changer.is_admin:
        return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    # Получаем рейтинг ученика
    rating = db.query(StudentRating).filter(
        StudentRating.student_id == student_id
    ).first()

    if not rating:
        rating = get_or_create_student_rating(db, student_id)
        db.commit()
        db.refresh(rating)

    # Сохраняем состояние до изменения
    score_before = rating.score

    # Применяем изменение
    new_score = max(0, min(10000, rating.score + score_change))
    rating.score = new_score
    rating.recalculate_grade()
    rating.last_updated_by = changer.id
    rating.updated_at = datetime.utcnow()

    if notes:
        rating.notes = notes

    # Изменение поведения
    if behavior_change is not None:
        rating.behavior_score = max(0, min(100, rating.behavior_score + behavior_change))

    # Записываем в историю
    change_record = StudentRatingChange(
        rating_id=rating.id,
        student_id=student_id,
        score_before=score_before,
        score_after=new_score,
        score_change=score_change,
        reason=reason,
        changed_by_id=changer.id,
    )
    db.add(change_record)
    db.commit()

    return {
        "status": "ok",
        "new_score": new_score,
        "new_grade": rating.grade,
        "change": score_change,
    }


# ==================== API: История рейтинга ====================

@router.get("/api/{student_id}/history")
async def get_rating_history(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """API: история изменений рейтинга ученика"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    # Ученик может смотреть только свою историю
    if current_user.role not in ("trainer", "admin") and not current_user.is_admin:
        if current_user.id != student_id:
            raise HTTPException(status_code=403, detail="Доступ запрещён")

    changes = db.query(StudentRatingChange).filter(
        StudentRatingChange.student_id == student_id
    ).order_by(StudentRatingChange.created_at.desc()).limit(100).all()

    return [
        {
            "id": c.id,
            "score_before": c.score_before,
            "score_after": c.score_after,
            "score_change": c.score_change,
            "reason": c.reason,
            "changed_by": c.changed_by.username if c.changed_by else "System",
            "created_at": c.created_at.strftime("%d.%m.%Y %H:%M"),
        }
        for c in changes
    ]


# ==================== API: Установка тренера ====================

@router.post("/api/set-coach")
async def set_student_coach(
    request: Request,
    student_id: int = Form(...),
    coach_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Установить тренера для ученика (админ)"""
    admin = get_current_user_from_cookie(request, db)
    if not admin or not admin.is_admin:
        return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    rating = db.query(StudentRating).filter(
        StudentRating.student_id == student_id
    ).first()

    if not rating:
        rating = get_or_create_student_rating(db, student_id, coach_id)
    else:
        rating.coach_id = coach_id

    db.commit()

    return {"status": "ok", "message": "Тренер установлен"}
