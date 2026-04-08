"""
Premium Subscription Service — управление подписками
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from models import get_db, User
from extended_models import Subscription
from auth import get_current_user_from_cookie
from utils import generate_csrf_token, validate_csrf_token

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
templates = Jinja2Templates(directory="templates")

# Тарифные планы
PLANS = {
    "monthly": {
        "name": "Ежемесячный",
        "price": 299,
        "currency": "₽",
        "duration_days": 30,
        "features": [
            "Расширенная статистика",
            "Приоритет в матчмейкинге",
            "Экспорт статистики (CSV)",
            "Кастомизация профиля",
            "Без рекламы",
            "Скидка 10% у тренеров",
        ]
    },
    "yearly": {
        "name": "Ежегодный",
        "price": 2499,
        "currency": "₽",
        "duration_days": 365,
        "features": [
            "Все функции Monthly",
            "Экономия 33%",
            "Эксклюзивный бейдж",
            "Ранний доступ к новым функциям",
            "Скидка 20% у тренеров",
            "Приоритетная поддержка",
        ]
    },
}


def is_premium(user: User, db: Session) -> bool:
    """Проверить, есть ли у пользователя активная подписка"""
    sub = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active",
        Subscription.expires_at > datetime.utcnow()
    ).first()
    return sub is not None


@router.get("/", response_class=HTMLResponse)
async def subscriptions_page(request: Request, db: Session = Depends(get_db)):
    """Страница управления подпиской"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login?next=/subscriptions")

    current_sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status.in_(["active", "cancelled"])
    ).order_by(Subscription.started_at.desc()).first()

    premium = current_sub and current_sub.is_active if current_sub else False

    return templates.TemplateResponse("subscriptions.html", {
        "request": request,
        "current_user": current_user,
        "plans": PLANS,
        "current_subscription": current_sub,
        "is_premium": premium,
        "csrf_token": generate_csrf_token(),
    })


@router.post("/create")
async def create_subscription(
    request: Request,
    plan: str = Form(...),
    db: Session = Depends(get_db)
):
    """Создать подписку (заглушка для интеграции с платёжной системой)"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return JSONResponse({"error": "Требуется авторизация"}, status_code=401)

    if plan not in PLANS:
        return JSONResponse({"error": "Неверный план"}, status_code=400)

    plan_data = PLANS[plan]
    now = datetime.utcnow()

    # Проверяем существующую активную подписку
    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()

    if existing:
        return JSONResponse({"error": "У вас уже есть активная подписка"}, status_code=400)

    # Создаём подписку
    subscription = Subscription(
        user_id=current_user.id,
        plan=plan,
        status="active",
        started_at=now,
        expires_at=now + timedelta(days=plan_data["duration_days"]),
        payment_provider="demo",  # TODO: yookassa / stripe
        auto_renew=True,
    )
    db.add(subscription)
    db.commit()

    return {
        "status": "created",
        "message": f"Подписка {plan_data['name']} активирована",
        "expires_at": subscription.expires_at.isoformat(),
    }


@router.post("/cancel")
async def cancel_subscription(
    request: Request,
    db: Session = Depends(get_db)
):
    """Отменить подписку"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return JSONResponse({"error": "Требуется авторизация"}, status_code=401)

    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()

    if not subscription:
        return JSONResponse({"error": "Активная подписка не найдена"}, status_code=404)

    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.utcnow()
    subscription.auto_renew = False
    db.commit()

    return {"status": "cancelled", "message": "Подписка отменена. Доступ сохранён до " + subscription.expires_at.strftime("%d.%m.%Y")}


@router.get("/api/check")
async def check_premium_status(
    request: Request,
    db: Session = Depends(get_db)
):
    """API: проверка статуса подписки"""
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return {"premium": False}

    return {
        "premium": is_premium(current_user, db),
        "user_id": current_user.id,
    }
