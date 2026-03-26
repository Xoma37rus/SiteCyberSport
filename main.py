from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from sqlalchemy.orm import Session, joinedload
from models import create_tables, init_disciplines, News, Discipline, Tournament, get_db
from auth import router as auth_router
from admin import router as admin_router
from admin_teams import router as teams_router
from admin_tournaments import router as admin_tournaments_router
from news import router as news_router
from disciplines import router as disciplines_router
from tournaments import router as tournaments_router
from api import router as api_router

app = FastAPI(title="EasyCyberPro - Киберспортивная платформа")

# CORS для cookie
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Отключаем кэширование шаблонов для разработки
from jinja2 import FileSystemLoader, ChoiceLoader
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.loader = ChoiceLoader([
    FileSystemLoader(BASE_DIR / "templates"),
])
templates.env.auto_reload = True
templates.env.cache_size = 0

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(teams_router)
app.include_router(admin_tournaments_router)
app.include_router(news_router)
app.include_router(disciplines_router)
app.include_router(tournaments_router)
app.include_router(api_router)

create_tables()
init_disciplines()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "EasyCyberPro"}


@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    # Получаем последние 3 новости для главной
    news_list = db.query(News).filter(News.is_published == True).order_by(News.created_at.desc()).limit(3).all()

    # Получаем дисциплины с командами и турнирами
    disciplines = db.query(Discipline).options(
        joinedload(Discipline.teams),
        joinedload(Discipline.tournaments)
    ).filter(Discipline.is_active == True).all()

    # Получаем турниры
    tournaments = db.query(Tournament).options(
        joinedload(Tournament.discipline)
    ).order_by(Tournament.start_date.desc()).limit(3).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "news_list": news_list,
        "disciplines": disciplines,
        "tournaments": tournaments
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
