---
name: tdd-agent-master
description: Master of Test-Driven Development (TDD) using pytest, pytest-asyncio, and httpx TestClient for FastAPI.
---

# TDD Agent Master (V2: FastAPI + pytest)

This skill mandates a Test-First approach for all business logic and API endpoints in the Pulse platform.

## 1. Core Principles
- **No Code Without Tests**: For every new Service method or API route, the test file (`test_*.py`) must be written/updated FIRST.
- **Isolation**: Tests should not rely on external live APIs (like MoySklad). Use `unittest.mock` and `pytest.fixture` for mocking.
- **Database Modularity**: Use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`) for tests. Reset state via `@pytest.fixture(autouse=True)` to prevent leakage.

## 2. Tools
- **pytest**: Primary test runner. Use `describe`-style classes, `test_` functions, and `assert` statements.
- **pytest-asyncio**: Run async test functions with `asyncio_mode = "auto"` (configured in `pyproject.toml`).
- **httpx AsyncClient**: Test FastAPI routes using `httpx.AsyncClient` with `ASGITransport`:
  ```python
  from httpx import AsyncClient, ASGITransport
  from app.main import app

  async def test_get_cash_flow():
      transport = ASGITransport(app=app)
      async with AsyncClient(transport=transport, base_url="http://test") as client:
          response = await client.get("/api/v1/financial/cash-flow", params={...})
          assert response.status_code == 200
  ```
- **factory-boy**: Create test fixtures for SQLAlchemy models (configured in `pyproject.toml`).

## 3. Workflow for New Features
1. Read the specification (`spec.md`) — specifically the Pydantic schemas (Section 14) and API endpoints.
2. Create/Update `tests/test_<module>.py` (e.g., `tests/test_financial.py`).
3. Write failing tests (Red) — including edge cases (empty data, invalid dates, auth failures).
4. Implement the minimal code in `app/services/` and `app/routers/` to pass the tests (Green).
5. Refactor while keeping tests passing.

## 4. Test Organization
```
tests/
├── conftest.py          # Shared fixtures: async client, test DB, mock user
├── fixtures/            # JSON fixtures for MoySklad API responses
├── test_financial.py    # ОДДС, ОПиУ, Баланс 
├── test_working_capital.py  # CCC, A/R, A/P
├── test_inventory.py    # ABC/XYZ, GMROI
├── test_analytics.py    # LTV/CAC, Когорты
├── test_supply_chain.py # OTIF
├── test_auth.py         # JWT login/refresh/RBAC
└── test_sync.py         # Webhook processing, sync logic
```

## 5. Coverage Requirements
- **services/**: ≥ 80% coverage
- **repositories/**: ≥ 60% coverage
- **routers/**: ≥ 70% coverage (HTTP codes, auth, validation)
