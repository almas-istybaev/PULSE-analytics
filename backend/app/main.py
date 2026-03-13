"""
Pulse Backend — Точка входа FastAPI приложения.

Настраивает приложение, middleware, роутеры, rate limiting,
security headers и SQLite WAL режим при старте.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import event, text

from app.core.config import settings
from app.core.database import engine, async_session_factory
from app.core.exceptions import register_exception_handlers
from app.models.base import Base

# ──────────────────────────────────────────────
# Структурированное логирование
# ──────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger(__name__)

# ──────────────────────────────────────────────
# Rate Limiter (slowapi)
# ──────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


# ──────────────────────────────────────────────
# SQLite PRAGMA — каждое подключение
# ──────────────────────────────────────────────
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
    """Настраивает SQLite PRAGMA для максимальной производительности.

    WAL-режим критически важен для конкурентного чтения при аналитических запросах.
    busy_timeout предотвращает SQLITE_BUSY при параллельных запросах.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-65536")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA mmap_size=268435456")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA auto_vacuum=INCREMENTAL")
    cursor.close()


# ──────────────────────────────────────────────
# Lifespan — запуск и остановка
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управляет жизненным циклом FastAPI.

    Startup: создаёт таблицы, верифицирует WAL, запускает APScheduler.
    Shutdown: останавливает планировщик, закрывает пул соединений.
    """
    # ── STARTUP ──
    logger.info("Запуск Pulse Backend", version="1.1.0", environment=settings.ENVIRONMENT)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        result = await session.execute(text("PRAGMA journal_mode"))
        journal_mode = result.scalar()
        logger.info("SQLite journal_mode", mode=journal_mode)

    # APScheduler — фоновые задачи синхронизации
    from app.services.scheduler import start_scheduler
    start_scheduler()

    logger.info("Pulse Backend запущен ✓")
    yield

    # ── SHUTDOWN ──
    from app.services.scheduler import stop_scheduler
    stop_scheduler()
    await engine.dispose()
    logger.info("Pulse Backend остановлен ✓")


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────
app = FastAPI(
    title="Pulse Analytics API",
    description="Финансово-коммерческая аналитика для бизнеса Казахстана",
    version="1.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────
# Rate Limiting
# ──────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ──────────────────────────────────────────────
# Exception Handlers
# ──────────────────────────────────────────────
register_exception_handlers(app)

# ──────────────────────────────────────────────
# Security Headers Middleware
# ──────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """Добавляет HTTP security headers к каждому ответу.

    Реализует OWASP-рекомендованные заголовки безопасности
    для защиты от XSS, clickjacking и MIME-sniffing атак.
    """
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
    return response


# ──────────────────────────────────────────────
# Middleware
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# ──────────────────────────────────────────────
# Роутеры API v1
# ──────────────────────────────────────────────
from app.api.v1.router import api_router  # noqa: E402
app.include_router(api_router, prefix="/api/v1")

# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────
@app.get("/health", tags=["Система"])
async def health_check() -> dict[str, str]:
    """Проверка работоспособности сервиса.

    Returns:
        Статус сервиса и версия.
    """
    return {"status": "ok", "service": "pulse-backend", "version": "1.1.0"}


@app.get("/api/v1/ping", tags=["Система"])
async def ping() -> dict[str, str]:
    """Простая проверка доступности API (без auth).

    Returns:
        Ответ pong для измерения latency.
    """
    return {"message": "pong"}
