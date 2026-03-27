import logging
from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from models import create_tables, init_disciplines, News, Discipline, Tournament, get_db
from auth import router as auth_router
from admin import router as admin_router
from admin_teams import router as teams_router
from admin_tournaments import router as admin_tournaments_router
from news import router as news_router, public_router as public_news_router
from disciplines import router as disciplines_router
from tournaments import router as tournaments_router
from api import router as api_router
from profile import router as profile_router
from config import settings
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Настройка rate limiting
limiter = Limiter(key_func=get_remote_address)
limiter.default_limits = [
    f"{settings.rate_limit_per_minute}/minute",
    f"{settings.rate_limit_burst}/second"
]

# Настройка logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="EasyCyberPro - Киберспортивная платформа")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
app.include_router(public_news_router)
app.include_router(disciplines_router)
app.include_router(tournaments_router)
app.include_router(api_router)
app.include_router(profile_router)

try:
    create_tables()
    init_disciplines()
    logger.info("Database tables created and disciplines initialized")
except Exception as e:
    logger.error(f"Database initialization error: {e}")
    raise


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
