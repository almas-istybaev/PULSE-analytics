"""
FastAPI зависимости для аутентификации и авторизации (RBAC).

Определяет get_current_user и require_role фабрику зависимостей.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security.jwt import decode_token

# HTTP Bearer схема аутентификации
bearer_scheme = HTTPBearer(auto_error=False)

# Роли платформы Pulse (в порядке убывания привилегий)
VALID_ROLES = {"admin", "ceo", "cfo", "cco", "buyer", "investor"}


class AuthenticatedUser:
    """Текущий аутентифицированный пользователь из JWT payload."""

    def __init__(self, user_id: str, email: str, role: str) -> None:
        self.user_id = user_id
        self.email = email
        self.role = role


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthenticatedUser:
    """Извлекает и верифицирует текущего пользователя из Bearer-токена.

    Вызывается через `Depends(get_current_user)` на каждом защищённом роуте.

    Args:
        credentials: HTTP Authorization Bearer credentials.

    Returns:
        AuthenticatedUser с данными из JWT payload.

    Raises:
        HTTPException 401: Токен отсутствует, невалиден или истёк.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_TOKEN", "message": "Authorization token is required"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise JWTError("Not an access token")

        user_id: str = payload.get("sub", "")
        email: str = payload.get("email", "")
        role: str = payload.get("role", "")

        if not user_id or role not in VALID_ROLES:
            raise JWTError("Invalid payload")

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token is invalid or expired"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(user_id=user_id, email=email, role=role)


def require_role(*allowed_roles: str):
    """Фабрика зависимостей для проверки ролей (RBAC).

    Usage:
        @router.get("/...", dependencies=[Depends(require_role("admin", "cfo"))])

    Args:
        *allowed_roles: Роли, которым разрешён доступ.

    Returns:
        FastAPI Dependency, проверяющий роль текущего пользователя.

    Raises:
        HTTPException 403: Если роль пользователя не входит в allowed_roles.
    """
    async def _check_role(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> AuthenticatedUser:
        if current_user.role not in allowed_roles and "admin" not in allowed_roles:
            # admin всегда имеет доступ
            if current_user.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "INSUFFICIENT_PERMISSIONS",
                        "message": f"Role '{current_user.role}' is not allowed. Required: {list(allowed_roles)}",
                    },
                )
        return current_user

    return _check_role


# Аннотация для удобного использования в эндпоинтах
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
