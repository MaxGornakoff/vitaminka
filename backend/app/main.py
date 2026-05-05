from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api import chat, health, shops
from app.admin import create_admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Vitaminka Assistant запущен")
    yield
    # Shutdown
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
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роуты
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(shops.router, prefix="/api/shops", tags=["shops"])

@app.get("/")
async def root():
    return {"message": "Vitaminka Assistant API"}
