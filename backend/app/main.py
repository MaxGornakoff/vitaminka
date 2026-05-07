from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
import logging

from app.core.config import settings
from app.api import chat, health, shops
from app.admin import create_admin

logger = logging.getLogger(__name__)


def _run_catalog_sync_all():
    """Проверяем каждый час — у каких магазинов подошло время синхронизации."""
    from app.db.session import SessionLocal
    from app.models.shop import Shop
    from app.services.feed_sync import sync_shop_catalog
    from datetime import datetime, timedelta

    db = SessionLocal()
    try:
        active_shops = (
            db.query(Shop)
            .filter(Shop.is_active == True, Shop.catalog_url != None, Shop.catalog_url != "")
            .all()
        )
        now = datetime.utcnow()
        for shop in active_shops:
            interval_h = shop.catalog_sync_interval_hours or settings.CATALOG_SYNC_INTERVAL_HOURS
            # Если магазин ещё ни разу не синкался — синкать сразу
            due_at = (shop.last_indexed + timedelta(hours=interval_h)) if shop.last_indexed else now
            if now >= due_at:
                try:
                    result = asyncio.run(sync_shop_catalog(shop, db))
                    logger.info("Автосинк %s (интервал %dч): %d товаров", shop.shop_id, interval_h, result.synced_count)
                except Exception as e:
                    logger.warning("Автосинк %s завершился с ошибкой: %s", shop.shop_id, e)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _run_catalog_sync_all,
        trigger="interval",
        hours=1,  # проверяем каждый час, но каждый магазин синкается по своему интервалу
        id="catalog_sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Планировщик запущен: проверка синхронизации каждый час")
    print("🚀 Vitaminka Assistant запущен")
    yield
    # Shutdown
    scheduler.shutdown(wait=False)
    print("🛑 Vitaminka Assistant остановлен")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

# Admin panel
create_admin(app)

# Session middleware (needed for admin auth)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы (widget.js и др.)
_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# Роуты
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(shops.router, prefix="/api/shops", tags=["shops"])

@app.get("/")
async def root():
    return {"message": "Vitaminka Assistant API"}
