"""
Shared pytest fixtures для всех тестов Pulse backend.

Настраивает in-memory SQLite БД, тестовый HTTPx-клиент и mock users.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security.jwt import create_access_token, hash_password
from app.models.base import Base, User

# ─────────────────────────────────────────────
# Тестовая БД (in-memory SQLite)
# ─────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Свежая тестовая БД для каждого теста.

    Создаёт все таблицы, выдаёт сессию, затем удаляет всё.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionFactory() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Тестовый AsyncClient с overridden get_db и без реальных сетевых запросов."""
    from app.core.database import get_db
    from app.main import app

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    """Создаёт тестового пользователя с ролью admin."""
    user = User(
        id=str(uuid.uuid4()),
        email="admin@test.pulse",
        hashed_password=hash_password("testpass123"),
        full_name="Test Admin",
        role="admin",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def cfo_user(db: AsyncSession) -> User:
    """Создаёт тестового пользователя с ролью cfo."""
    user = User(
        id=str(uuid.uuid4()),
        email="cfo@test.pulse",
        hashed_password=hash_password("testpass123"),
        full_name="Test CFO",
        role="cfo",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    """JWT access-токен для admin пользователя."""
    return create_access_token({
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "role": admin_user.role,
    })


@pytest.fixture
def cfo_token(cfo_user: User) -> str:
    """JWT access-токен для cfo пользователя."""
    return create_access_token({
        "sub": str(cfo_user.id),
        "email": cfo_user.email,
        "role": cfo_user.role,
    })


@pytest.fixture
def auth_headers(admin_token: str) -> dict[str, str]:
    """HTTP-заголовки с Bearer токеном для тестовых запросов."""
    return {"Authorization": f"Bearer {admin_token}"}
