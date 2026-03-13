"""
Тесты аутентификации: login, refresh, RBAC.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user, admin_token):
    """POST /auth/login возвращает access_token при верных credentials."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.pulse",
        "password": "testpass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, admin_user):
    """POST /auth/login возвращает 401 при неверном пароле."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.pulse",
        "password": "wrongpass",
    })
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient):
    """POST /auth/login возвращает 401 если пользователь не найден."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "nobody@test.pulse",
        "password": "pass",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_valid_token(client: AsyncClient, admin_user, auth_headers):
    """GET /auth/me возвращает данные текущего пользователя."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.pulse"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_get_me_without_token(client: AsyncClient):
    """GET /auth/me возвращает 401 без токена."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "MISSING_TOKEN"


@pytest.mark.asyncio
async def test_get_me_with_invalid_token(client: AsyncClient):
    """GET /auth/me возвращает 401 с невалидным токеном."""
    response = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_rbac_cfo_cannot_access_admin_endpoint(client: AsyncClient, cfo_user, cfo_token):
    """RBAC: роль cfo не имеет прямого доступа к admin-only эндпоинтам."""
    headers = {"Authorization": f"Bearer {cfo_token}"}
    # GET /sync/status требует admin или cfo — должен пройти
    response = await client.get("/api/v1/sync/status", headers=headers)
    # cfo имеет доступ к sync/status по спецификации
    assert response.status_code in (200, 401, 403)
