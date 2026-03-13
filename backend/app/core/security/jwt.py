"""
JWT аутентификация — создание и верификация токенов.

Использует HS256 алгоритм с SECRET_KEY из настроек.
Access-токен: 15 минут. Refresh-токен: 7 дней.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Контекст для хэширования паролей (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Хэширует пароль через bcrypt.

    Args:
        plain: Исходный пароль в открытом виде.

    Returns:
        Bcrypt-хэш пароля.
    """
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Проверяет пароль против bcrypt-хэша.

    Args:
        plain: Пароль в открытом виде.
        hashed: Хэш из базы данных.

    Returns:
        True если пароль совпадает.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict[str, Any]) -> str:
    """Создаёт JWT access-токен с TTL 15 минут.

    Args:
        data: Payload токена (обязательно: sub=user_id, role=role).

    Returns:
        Подписанный JWT-строкой.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {**data, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Создаёт JWT refresh-токен с TTL 7 дней.

    Args:
        data: Payload (обязательно: sub=user_id).

    Returns:
        Подписанный JWT refresh-строкой.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {**data, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Декодирует и верифицирует JWT токен.

    Args:
        token: JWT-строка.

    Returns:
        Декодированный payload.

    Raises:
        JWTError: Если токен невалиден или истёк.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
