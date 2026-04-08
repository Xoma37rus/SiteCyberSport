"""
Match Reports & Verification — система жалоб и верификации результатов
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Optional

from models import get_db, User, Match
from extended_models import MatchReport, ReportType, ReportStatus
from auth import get_current_user_from_cookie
from utils import generate_csrf_token, validate_csrf_token

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory="templates")


@router.post("/create")
async def create_report(
    request: Request,
    report_type: str = Form(...),
    description: str = Form(...),
    match_id: Optional[int] = Form(None),
    reported_user_id: Optional[int] = Form(None),
    evidence_urls: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Создать жалобу"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return JSONResponse({"error": "Требуется авторизация"}, status_code=401)

    # Валидация
    if not description or len(description) < 20:
        return JSONResponse({"error": "Описание должно содержать минимум 20 символов"}, status_code=400)

    try:
        rtype = ReportType(report_type)
    except ValueError:
        return JSONResponse({"error": "Неверный тип жалобы"}, status_code=400)

    report = MatchReport(
        reporter_id=current_user.id,
        reported_user_id=reported_user_id,
        match_id=match_id,
        report_type=rtype,
        description=description,
        evidence_urls=evidence_urls,
        status=ReportStatus.PENDING,
    )
    db.add(report)
    db.commit()

    return {"status": "created", "message": "Жалоба отправлена на рассмотрение"}


@router.get("/", response_class=HTMLResponse)
async def my_reports(request: Request, db: Session = Depends(get_db)):
    """Мои жалобы"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login")

    reports = db.query(MatchReport).filter(
        MatchReport.reporter_id == current_user.id
    ).order_by(MatchReport.created_at.desc()).limit(50).all()

    csrf_token = generate_csrf_token()
    return templates.TemplateResponse("my_reports.html", {
        "request": request,
        "current_user": current_user,
        "reports": reports,
        "csrf_token": csrf_token,
        "report_types": [r.value for r in ReportType],
    })


# ==================== ADMIN: Управление жалобами ====================

admin_router = APIRouter(prefix="/admin/reports", tags=["admin-reports"])


@admin_router.get("/", response_class=HTMLResponse)
async def admin_reports(request: Request, db: Session = Depends(get_db)):
    """Админ-панель: список жалоб"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    status_filter = request.query_params.get("status", "pending")

    query = db.query(MatchReport).options(
        joinedload(MatchReport.reporter),
        joinedload(MatchReport.reported_user),
        joinedload(MatchReport.match)
    )

    if status_filter != "all":
        query = query.filter(MatchReport.status == ReportStatus(status_filter))

    reports = query.order_by(MatchReport.created_at.desc()).all()

    return templates.TemplateResponse("admin/reports.html", {
        "request": request,
        "current_user": current_user,
        "reports": reports,
        "status_filter": status_filter,
    })


@admin_router.post("/{report_id}/resolve")
async def resolve_report(
    report_id: int,
    request: Request,
    resolution: str = Form(...),
    status: str = Form("resolved"),
    db: Session = Depends(get_db)
):
    """Обработать жалобу"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    report = db.query(MatchReport).filter(MatchReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")

    report.status = ReportStatus(status)
    report.resolution = resolution
    report.admin_notes = f"Обработана администратором {current_user.username}"
    db.commit()

    return {"status": "ok", "message": "Жалоба обработана"}


@admin_router.post("/{report_id}/dismiss")
async def dismiss_report(
    report_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Отклонить жалобу"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    report = db.query(MatchReport).filter(MatchReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")

    report.status = ReportStatus.DISMISSED
    report.resolution = "Отклонено администратором"
    db.commit()

    return {"status": "ok", "message": "Жалоба отклонена"}
