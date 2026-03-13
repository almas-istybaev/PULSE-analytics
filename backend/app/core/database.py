"""
Настройка асинхронного подключения к SQLite через SQLAlchemy 2.0.

WAL-режим настраивается через event listener в main.py при каждом подключении.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Асинхронный движок — единственный экземпляр на всё приложение
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,       # SQL-логи только в режиме отладки
    pool_pre_ping=True,        # Проверка соединения перед использованием
    pool_size=5,               # Размер пула для SQLite (оптимально)
    max_overflow=10,           # Дополнительные соединения при нагрузке
    connect_args={
        "check_same_thread": False,  # Обязательно для aiosqlite
        "timeout": 30,               # Таймаут ожидания блокировки (секунды)
    },
)

# Фабрика асинхронных сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Не обновлять объекты после commit (async best practice)
)


async def get_db():
    """FastAPI dependency — предоставляет асинхронную сессию БД.

    Yields:
        AsyncSession: Сессия с автоматическим закрытием и откатом при ошибке.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
