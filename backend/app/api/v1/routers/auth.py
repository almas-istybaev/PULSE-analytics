"""
Auth router: login, refresh, logout, me.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.base import User

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


# ─────────────────────────────────
# Схемы
# ─────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 минут в секундах


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    is_active: bool


# ─────────────────────────────────
# Endpoints
# ─────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Аутентификация по email + пароль. Возвращает JWT access и refresh токены.

    Args:
        body: Email и пароль пользователя.
        db: Асинхронная сессия БД.

    Returns:
        JWT access-токен (TTL 15 мин).

    Raises:
        HTTPException 401: Неверные учётные данные.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ACCOUNT_DISABLED", "message": "Account is disabled"},
        )

    # Обновляем last_login_at
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    access = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return TokenResponse(access_token=access)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest) -> TokenResponse:
    """Обновляет access-токен по refresh-токену.

    Args:
        body: Refresh токен.

    Returns:
        Новый access-токен.

    Raises:
        HTTPException 401: Refresh-токен невалиден или истёк.
    """
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise JWTError("Not a refresh token")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or expired"},
        )

    access = create_access_token({
        "sub": payload["sub"],
        "email": payload.get("email", ""),
        "role": payload.get("role", ""),
    })
    return TokenResponse(access_token=access)


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Выход из системы. Клиент должен удалить токены локально.

    Returns:
        Подтверждение выхода.

    Note:
        При переходе на refresh-токены в HttpOnly cookie —
        здесь нужно будет очищать cookie.
    """
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Возвращает данные текущего аутентифицированного пользователя.

    Args:
        current_user: Декодированные данные из JWT.
        db: Асинхронная сессия БД.

    Returns:
        Профиль пользователя с ролью.

    Raises:
        HTTPException 404: Пользователь не найден в БД.
    """
    result = await db.execute(select(User).where(User.id == current_user.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )
