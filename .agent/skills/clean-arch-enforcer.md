---
name: clean-arch-enforcer
description: Правила строгого разделения ответственности — Clean Architecture для Pulse backend
---

# Clean Architecture Enforcer

## Архитектурные слои

Pulse backend СТРОГО следует четырёхслойной архитектуре:

```
HTTP Request
     │
     ▼
┌─────────────┐
│   ROUTERS   │  ← FastAPI Routers (app/api/v1/)
│  (Transport) │    Только: валидация входа, вызов сервиса, формирование ответа
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  SERVICES   │  ← Business Logic (app/services/)
│ (Use Cases) │    Только: бизнес-правила, оркестрация, расчёты
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ REPOSITORIES │  ← Data Access (app/repositories/)
│ (Data Layer) │    Только: запросы к БД, ORM-операции
└──────┬───────┘
       │
       ▼
┌─────────────┐
│   MODELS    │  ← SQLAlchemy Models (app/models/)
│  (DB Layer) │    Только: определения таблиц, связей
└─────────────┘
```

---

## Правила для каждого слоя

### 1. Routers (`app/api/v1/`)

```python
# ✅ Правильно — только транспортный слой
@router.get("/reports/ccc", response_model=CCCReportSchema)
async def get_ccc_report(
    period: DateRangeParams = Depends(),
    service: WorkingCapitalService = Depends(get_working_capital_service),
) -> CCCReportSchema:
    """Возвращает отчёт по циклу конвертации денежных средств."""
    return await service.calculate_ccc(period.start_date, period.end_date)

# ❌ Запрещено в роутерах:
# - Прямые запросы к БД (db.execute(...))
# - Бизнес-логика (if revenue > expenses: ...)
# - HTTP-запросы к внешним API
```

### 2. Services (`app/services/`)

```python
# ✅ Правильно — только бизнес-логика
class WorkingCapitalService:
    def __init__(self, repo: WorkingCapitalRepository) -> None:
        self._repo = repo

    async def calculate_ccc(self, start: date, end: date) -> CCCReportSchema:
        """Рассчитывает CCC = DSO + DIO - DPO."""
        raw = await self._repo.get_working_capital_data(start, end)
        dso = raw.receivables / (raw.revenue / 365)
        dio = raw.inventory / (raw.cogs / 365)
        dpo = raw.payables / (raw.cogs / 365)
        return CCCReportSchema(ccc=dso + dio - dpo, dso=dso, dio=dio, dpo=dpo)

# ❌ Запрещено в сервисах:
# - ORM-запросы (session.execute(select(Model)))
# - Формирование HTTP-ответов (Response, JSONResponse)
# - Прямой доступ к request/response объектам
```

### 3. Repositories (`app/repositories/`)

```python
# ✅ Правильно — только работа с БД
class WorkingCapitalRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_working_capital_data(self, start: date, end: date) -> WorkingCapitalData:
        """Получает агрегированные данные для расчёта оборотного капитала."""
        result = await self._db.execute(
            select(...)
            .where(Invoice.date.between(start, end))
        )
        return result.scalar_one_or_none()

# ❌ Запрещено в репозиториях:
# - Бизнес-расчёты (CCC, EBITDA, LTV формулы)
# - Вызов других сервисов
# - Обращение к внешним API
```

### 4. Models (`app/models/`)

```python
# ✅ Правильно — только ORM-определения
class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

# ❌ Запрещено в моделях:
# - Методы с бизнес-логикой
# - Прямые запросы к БД внутри модели
# - Импорты из services или repositories
```

---

## Структура файлов проекта

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # Главный роутер
│   │       ├── financial.py       # Финансовые отчёты
│   │       ├── inventory.py       # Складские отчёты
│   │       ├── analytics.py       # Аналитика
│   │       └── sync.py            # Синхронизация МойСклад
│   ├── services/
│   │   ├── financial_service.py
│   │   ├── inventory_service.py
│   │   ├── analytics_service.py
│   │   └── moysklad_sync_service.py
│   ├── repositories/
│   │   ├── financial_repository.py
│   │   ├── inventory_repository.py
│   │   └── analytics_repository.py
│   ├── models/
│   │   ├── base.py
│   │   ├── invoice.py
│   │   ├── product.py
│   │   ├── counterparty.py
│   │   └── stock.py
│   ├── schemas/
│   │   ├── financial.py
│   │   ├── inventory.py
│   │   └── analytics.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── dependencies.py
│   └── main.py
├── alembic/
├── tests/
└── pyproject.toml
```

---

## Dependency Injection (FastAPI)

```python
# app/core/dependencies.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

def get_financial_service(db: AsyncSession = Depends(get_db)) -> FinancialService:
    repo = FinancialRepository(db)
    return FinancialService(repo)
```

**Правило**: Зависимости инжектируются только через `Depends()`. Прямое создание сервисов в роутерах — запрещено.

---

## Запрещённые паттерны

| Паттерн | Проблема |
|---------|----------|
| `router` напрямую обращается к `db` | Нарушение разделения слоёв |
| `service` импортирует другой `service` напрямую | Должны общаться через интерфейсы |
| `model` содержит бизнес-методы | Anemic Domain Model нарушение |
| Логика в Pydantic validators | Validators — только валидация формата |
| Circular imports между слоями | Признак нарушения архитектуры |
