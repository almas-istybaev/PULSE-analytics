"""
Pulse Backend — Точка входа FastAPI приложения.

Настраивает приложение, middleware, роутеры и SQLite WAL режим при старте.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import event, text

from app.core.config import settings
from app.core.database import engine, async_session_factory
from app.core.exceptions import register_exception_handlers
from app.models.base import Base

# ──────────────────────────────────────────────
# Настройка структурированного логирования
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
# SQLite PRAGMA — устанавливается при каждом подключении
# ──────────────────────────────────────────────
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
    """Настраивает SQLite PRAGMA для максимальной производительности.

    Вызывается автоматически при каждом новом подключении к БД.
    WAL-режим критически важен для конкурентного чтения при аналитических запросах.
    busy_timeout предотвращает SQLITE_BUSY при параллельных запросах.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")        # Журнал записи вперёд
    cursor.execute("PRAGMA synchronous=NORMAL")       # Баланс скорости и надёжности
    cursor.execute("PRAGMA cache_size=-65536")        # 64 МБ кеша страниц
    cursor.execute("PRAGMA foreign_keys=ON")          # Проверка внешних ключей
    cursor.execute("PRAGMA busy_timeout=5000")        # 5 сек ожидание при блокировке
    cursor.execute("PRAGMA mmap_size=268435456")      # 256 МБ memory-mapped I/O
    cursor.execute("PRAGMA temp_store=MEMORY")        # Временные таблицы в RAM
    cursor.execute("PRAGMA auto_vacuum=INCREMENTAL")  # Постепенная дефрагментация
    cursor.close()


# ──────────────────────────────────────────────
# Lifespan — старт и остановка приложения
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управляет жизненным циклом FastAPI приложения.

    При старте:
    - Создаёт таблицы БД (если не существуют)
    - Верифицирует WAL-режим
    - Логирует конфигурацию

    При остановке:
    - Корректно закрывает пул соединений
    """
    # ── STARTUP ──
    logger.info(
        "Запуск Pulse Backend",
        version="1.1.0",
        environment=settings.ENVIRONMENT,
        database_url=settings.DATABASE_URL,
    )

    # Создание схемы БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Верификация WAL-режима
    async with async_session_factory() as session:
        result = await session.execute(text("PRAGMA journal_mode"))
        journal_mode = result.scalar()
        logger.info("Режим журнала SQLite", journal_mode=journal_mode)

        if journal_mode != "wal":
            logger.warning("WAL-режим не активен! Производительность может снизиться.")

    logger.info("Pulse Backend запущен успешно ✓")

    yield  # Приложение работает

    # ── SHUTDOWN ──
    logger.info("Остановка Pulse Backend...")
    await engine.dispose()
    logger.info("Соединения с БД закрыты ✓")


# ──────────────────────────────────────────────
# Создание FastAPI приложения
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
# Обработчики ошибок
# ──────────────────────────────────────────────
register_exception_handlers(app)

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
        Словарь со статусом сервиса и версией.
    """
    return {"status": "ok", "service": "pulse-backend", "version": "1.1.0"}


@app.get("/api/v1/ping", tags=["Система"])
async def ping() -> dict[str, str]:
    """Простая проверка доступности API.

    Returns:
        Ответ pong для проверки latency.
    """
    return {"message": "pong"}
