"""
Alembic environment — конфигурация для асинхронных миграций.

Использует async engine из app.core.database для поддержки aiosqlite.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Загружаем метаданные всех моделей
from app.models.base import Base

# Alembic Config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для автогенерации миграций
target_metadata = Base.metadata


def get_url() -> str:
    """Возвращает URL БД из переменной окружения или конфига Alembic."""
    from app.core.config import settings
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """Запускает миграции в offline-режиме (без подключения к БД).

    Используется для генерации SQL-скриптов без реального подключения.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:  # type: ignore[no-untyped-def]
    """Настраивает контекст и запускает миграции в online-режиме."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=True,  # SQLite требует batch-режим для ALTER TABLE
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Запускает миграции через асинхронный engine.

    aiosqlite требует async-подхода для подключения к SQLite.
    """
    connectable = create_async_engine(get_url())

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Точка входа для online-миграций через asyncio."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
