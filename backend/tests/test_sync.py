"""
Тесты webhook-обработчика и синхронизации.
"""
from __future__ import annotations

import hashlib
import hmac

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_webhook_without_signature_is_allowed_when_no_secret(client: AsyncClient):
    """POST /sync/webhook проходит без подписи если WEBHOOK_SECRET не задан."""
    payload = {"events": []}
    response = await client.post("/api/v1/sync/webhook", json=payload)
    # Должен вернуть 200 (при пустом secret — верификация пропускается)
    assert response.status_code == 200
    data = response.json()
    assert data["events_received"] == 0
    assert data["events_processed"] == 0


@pytest.mark.asyncio
async def test_webhook_with_no_events(client: AsyncClient):
    """POST /sync/webhook с пустым events[] возвращает 0 processed."""
    response = await client.post("/api/v1/sync/webhook", json={"events": []})
    assert response.status_code == 200
    assert response.json()["events_processed"] == 0


@pytest.mark.asyncio
async def test_webhook_with_unsupported_entity(client: AsyncClient):
    """POST /sync/webhook игнорирует неизвестные типы сущностей."""
    events = [{"meta": {"type": "unknown_entity", "href": ""}, "action": "CREATE"}]
    response = await client.post("/api/v1/sync/webhook", json={"events": events})
    assert response.status_code == 200
    assert response.json()["events_processed"] == 0


@pytest.mark.asyncio
async def test_sync_status_requires_auth(client: AsyncClient):
    """GET /sync/status требует аутентификации."""
    response = await client.get("/api/v1/sync/status")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_sync_status_returns_logs(client: AsyncClient, auth_headers):
    """GET /sync/status возвращает список логов."""
    response = await client.get("/api/v1/sync/status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert isinstance(data["logs"], list)
