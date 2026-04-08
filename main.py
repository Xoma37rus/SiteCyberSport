import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
from models import create_tables, init_disciplines, News, Discipline, Tournament, get_db
from auth import router as auth_router
from admin import router as admin_router
from admin_teams import router as teams_router
from admin_tournaments import router as admin_tournaments_router
from admin_coaches import router as admin_coaches_router
from news import router as news_router, public_router as public_news_router
from disciplines import router as disciplines_router
from tournaments import router as tournaments_router
from api import router as api_router
from profile import router as profile_router
from coach import router as coach_router
from leaderboard import router as leaderboard_router

# Новые модули
from matchmaking_service import router as matchmaking_router, matchmaking_service
from steam_auth import router as steam_auth_router
from discord_service import init_discord_bot
from websocket_manager import ws_manager
from ladders import router as ladders_router, create_daily_ladders
from reports import router as reports_router, admin_router as admin_reports_router
from subscriptions import router as subscriptions_router
from stats_service import router as stats_router
from student_rating import router as student_rating_router
from extended_models import create_extended_tables, init_default_achievements

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/Shutdown events"""
    # Startup
    logger.info("Starting EasyCyberPro...")

    # Создание таблиц
    try:
        create_tables()
        create_extended_tables()
        init_disciplines()
        init_default_achievements()
        logger.info("Database tables created and initialized")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    # Инициализация Discord
    if settings.discord_bot_token:
        init_discord_bot(
            token=settings.discord_bot_token,
            client_id=settings.discord_client_id,
            client_secret=settings.discord_client_secret
        )
        logger.info("Discord bot initialized")

    # Создание ежедневных ладдеров
    try:
        db = next(get_db())
        create_daily_ladders(db)
        db.close()
        logger.info("Daily ladders created")
    except Exception as e:
        logger.error(f"Failed to create daily ladders: {e}")

    # Запуск матчмейкинга
    if settings.matchmaking_enabled:
        asyncio.create_task(matchmaking_service.start())
        logger.info("Matchmaking service started")

    yield

    # Shutdown
    if settings.matchmaking_enabled:
        await matchmaking_service.stop()
    logger.info("EasyCyberPro shutdown")


app = FastAPI(
    title="EasyCyberPro - Киберспортивная платформа",
    version="3.0.0",
    description="Платформа для киберспортивных соревнований с системой рейтинга ELO, турнирами и тренерством",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Шаблоны
from jinja2 import FileSystemLoader, ChoiceLoader
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.loader = ChoiceLoader([
    FileSystemLoader(BASE_DIR / "templates"),
])
templates.env.auto_reload = True
templates.env.cache_size = 0

# ==================== Регистрируем все роутеры ====================

# Аутентификация и профиль
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(subscriptions_router)

# Админ-панель
app.include_router(admin_router)
app.include_router(teams_router)
app.include_router(admin_tournaments_router)
app.include_router(admin_coaches_router)
app.include_router(admin_reports_router)

# Контент
app.include_router(news_router)
app.include_router(public_news_router)
app.include_router(disciplines_router)
app.include_router(tournaments_router)
app.include_router(leaderboard_router)
app.include_router(ladders_router)

# API и интеграции
app.include_router(api_router)
app.include_router(matchmaking_router)
app.include_router(steam_auth_router)
app.include_router(reports_router)
app.include_router(stats_router)
app.include_router(student_rating_router)
app.include_router(coach_router)


# ==================== WebSocket ====================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint для real-time уведомлений"""
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            # Принимаем сообщения (heartbeat)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(user_id, websocket)


# ==================== PWA и Service Worker ====================

@app.get("/sw.js")
async def service_worker():
    """Service Worker для PWA"""
    from fastapi.responses import FileResponse
    return FileResponse(BASE_DIR / "static" / "sw.js", media_type="application/javascript")


@app.get("/manifest.json")
async def manifest():
    """PWA Manifest"""
    from fastapi.responses import FileResponse
    return FileResponse(BASE_DIR / "static" / "manifest.json", media_type="application/json")


# ==================== Основные страницы ====================

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "EasyCyberPro",
        "version": "3.0.0",
        "matchmaking": "enabled" if settings.matchmaking_enabled else "disabled",
        "discord": "configured" if settings.discord_bot_token else "not configured",
        "steam": "configured" if settings.steam_api_key else "not configured"
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    news_list = db.query(News).filter(News.is_published == True).order_by(News.created_at.desc()).limit(3).all()

    disciplines = db.query(Discipline).options(
        joinedload(Discipline.teams),
        joinedload(Discipline.tournaments)
    ).filter(Discipline.is_active == True).all()

    tournaments = db.query(Tournament).options(
        joinedload(Tournament.discipline)
    ).order_by(Tournament.start_date.desc()).limit(3).all()

    from auth import get_current_user_from_cookie
    current_user = get_current_user_from_cookie(request, db)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "news_list": news_list,
        "disciplines": disciplines,
        "tournaments": tournaments,
        "current_user": current_user
    })


@app.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions_page(request: Request, db: Session = Depends(get_db)):
    from auth import get_current_user_from_cookie
    current_user = get_current_user_from_cookie(request, db)
    from subscriptions import PLANS, is_premium

    premium = is_premium(current_user, db) if current_user else False

    return templates.TemplateResponse("subscriptions.html", {
        "request": request,
        "current_user": current_user,
        "plans": PLANS,
        "is_premium": premium,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
