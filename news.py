import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from models import User, News, get_db
from admin import get_current_admin_user, require_admin
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["news"])
templates = Jinja2Templates(directory="templates")

BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@router.post("/news/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Загрузка изображения для новости"""
    from admin import get_current_admin_user
    admin = get_current_admin_user(request, db)
    if not admin:
        return JSONResponse(status_code=403, content={"error": "Требуется авторизация"})

    try:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return JSONResponse(
                status_code=400,
                content={"error": f"Недопустимый формат. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"}
            )

        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = UPLOAD_DIR / unique_filename

        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        image_url = f"/static/uploads/{unique_filename}"
        return JSONResponse(content={"location": image_url})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Ошибка загрузки: {str(e)}"})


@router.get("/news", response_class=HTMLResponse)
async def admin_news_list(request: Request, db: Session = Depends(get_db)):
    """Список всех новостей в админке"""
    admin = require_admin(request, db)
    news_list = db.query(News).options(
        joinedload(News.author)
    ).order_by(News.created_at.desc()).all()
    return templates.TemplateResponse("admin/news_list.html", {
        "request": request,
        "admin": admin,
        "news_list": news_list
    })


@router.get("/news/create", response_class=HTMLResponse)
async def admin_news_create_page(request: Request, db: Session = Depends(get_db)):
    """Страница создания новости"""
    admin = require_admin(request, db)
    from utils import generate_csrf_token
    return templates.TemplateResponse("admin/news_form.html", {
        "request": request,
        "admin": admin,
        "news": None,
        "action": "create",
        "csrf_token": generate_csrf_token()
    })


@router.post("/news/create")
async def admin_news_create(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    excerpt: str = Form(None),
    image_url: str = Form(None),
    is_published: str = Form("on"),
    db: Session = Depends(get_db)
):
    """Создание новости"""
    admin = require_admin(request, db)

    news = News(
        title=title,
        content=content,
        excerpt=excerpt or title[:200],
        image_url=image_url,
        author_id=admin.id,
        is_published=(is_published == "on")
    )

    db.add(news)
    db.commit()

    return RedirectResponse("/admin/news", status_code=303)


@router.get("/news/{news_id}/edit", response_class=HTMLResponse)
async def admin_news_edit_page(request: Request, news_id: int, db: Session = Depends(get_db)):
    """Страница редактирования новости"""
    admin = require_admin(request, db)
    news = db.query(News).filter(News.id == news_id).first()

    if not news:
        raise HTTPException(status_code=404, detail="Новость не найдена")

    from utils import generate_csrf_token
    return templates.TemplateResponse("admin/news_form.html", {
        "request": request,
        "admin": admin,
        "news": news,
        "action": "edit",
        "csrf_token": generate_csrf_token()
    })


@router.post("/news/{news_id}/edit")
async def admin_news_edit(
    request: Request,
    news_id: int,
    title: str = Form(...),
    content: str = Form(...),
    excerpt: str = Form(None),
    image_url: str = Form(None),
    is_published: str = Form("on"),
    db: Session = Depends(get_db)
):
    """Редактирование новости"""
    admin = require_admin(request, db)
    news = db.query(News).filter(News.id == news_id).first()

    if not news:
        raise HTTPException(status_code=404, detail="Новость не найдена")

    news.title = title
    news.content = content
    news.excerpt = excerpt or title[:200]
    news.image_url = image_url
    news.is_published = (is_published == "on")
    news.updated_at = datetime.utcnow()

    db.commit()

    return RedirectResponse("/admin/news", status_code=303)


@router.post("/news/{news_id}/delete")
async def admin_news_delete(
    request: Request,
    news_id: int,
    db: Session = Depends(get_db)
):
    """Удаление новости"""
    admin = require_admin(request, db)
    news = db.query(News).filter(News.id == news_id).first()

    if not news:
        raise HTTPException(status_code=404, detail="Новость не найдена")

    db.delete(news)
    db.commit()

    return RedirectResponse("/admin/news", status_code=303)


@router.post("/news/{news_id}/toggle-publish")
async def admin_news_toggle_publish(
    request: Request,
    news_id: int,
    db: Session = Depends(get_db)
):
    """Переключить статус публикации"""
    admin = require_admin(request, db)
    news = db.query(News).filter(News.id == news_id).first()

    if not news:
        raise HTTPException(status_code=404, detail="Новость не найдена")

    news.is_published = not news.is_published
    news.updated_at = datetime.utcnow()
    db.commit()

    return RedirectResponse("/admin/news", status_code=303)
