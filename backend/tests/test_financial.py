"""
Тесты финансовых отчётов: ОДДС, ОПиУ, Баланс.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Demand, PaymentIn, PaymentOut


@pytest.mark.asyncio
async def test_cash_flow_empty_period(client: AsyncClient, auth_headers):
    """GET /financial/cash-flow возвращает нули при отсутствии данных."""
    response = await client.get(
        "/api/v1/financial/cash-flow",
        params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["operating"]["net"] == 0.0
    assert data["total_net"] == 0.0


@pytest.mark.asyncio
async def test_cash_flow_with_payments(client: AsyncClient, db: AsyncSession, auth_headers):
    """GET /financial/cash-flow учитывает входящие и исходящие платежи."""
    # Добавляем тестовые данные
    pin = PaymentIn(
        id=str(uuid.uuid4()),
        moysklad_id=str(uuid.uuid4()),
        moment=datetime(2024, 1, 15, tzinfo=timezone.utc),
        sum=Decimal("1000000"),
    )
    pout = PaymentOut(
        id=str(uuid.uuid4()),
        moysklad_id=str(uuid.uuid4()),
        moment=datetime(2024, 1, 20, tzinfo=timezone.utc),
        sum=Decimal("300000"),
        expense_type="OPEX",
    )
    db.add(pin)
    db.add(pout)
    await db.commit()

    response = await client.get(
        "/api/v1/financial/cash-flow",
        params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["operating"]["inflow"] == 1_000_000.0
    assert data["total_net"] > 0


@pytest.mark.asyncio
async def test_cash_flow_invalid_period(client: AsyncClient, auth_headers):
    """GET /financial/cash-flow возвращает 422 при end_date <= start_date."""
    response = await client.get(
        "/api/v1/financial/cash-flow",
        params={"start_date": "2024-12-31", "end_date": "2024-01-01"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_income_statement_returns_expected_fields(client: AsyncClient, auth_headers):
    """GET /financial/income-statement содержит обязательные поля."""
    response = await client.get(
        "/api/v1/financial/income-statement",
        params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    required_fields = {"revenue", "cogs", "gross_profit", "gross_margin_pct", "ebitda", "ebitda_margin_pct"}
    assert required_fields.issubset(data.keys())


@pytest.mark.asyncio
async def test_balance_sheet_returns_balanced(client: AsyncClient, auth_headers):
    """GET /financial/balance-sheet: активы = обязательства + капитал."""
    response = await client.get(
        "/api/v1/financial/balance-sheet",
        params={"start_date": "2024-01-01", "end_date": "2024-12-31"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "check" in data
    assert data["check"]["balanced"] is True


@pytest.mark.asyncio
async def test_financial_requires_auth(client: AsyncClient):
    """Финансовые эндпоинты требуют аутентификации."""
    response = await client.get(
        "/api/v1/financial/cash-flow",
        params={"start_date": "2024-01-01", "end_date": "2024-01-31"},
    )
    assert response.status_code == 401
