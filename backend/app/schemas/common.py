"""
Общие Pydantic-схемы для параметров и ответов API.

Базовые схемы повторно используются всеми модулями Pulse.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Generic, Literal, Self, TypeVar

from pydantic import BaseModel, Field, model_validator

# ─────────────────────────────────────────────
# Базовые параметры запросов
# ─────────────────────────────────────────────

class PeriodParams(BaseModel):
    """Параметры периода — используются во всех отчётных эндпоинтах.

    Validates:
        - end_date > start_date
        - Период не превышает 366 дней
    """

    start_date: date = Field(..., description="Начало периода (ISO 8601)")
    end_date: date = Field(..., description="Конец периода (ISO 8601)")
    store_id: uuid.UUID | None = Field(None, description="UUID склада (опционально)")
    currency: str = Field("KZT", description="Валюта отчёта")

    @model_validator(mode="after")
    def validate_period(self) -> Self:
        """Проверяет корректность диапазона дат."""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        if (self.end_date - self.start_date).days > 366:
            raise ValueError("Period too long (max 366 days)")
        return self


class GroupByParams(PeriodParams):
    """Расширенные параметры с группировкой по временному интервалу."""

    group_by: Literal["day", "week", "month"] = Field(
        "month", description="Группировка данных"
    )


class PaginationParams(BaseModel):
    """Курсорная пагинация для списков."""

    cursor: str | None = Field(None, description="Курсор для следующей страницы")
    limit: int = Field(50, ge=1, le=200, description="Количество записей")


# ─────────────────────────────────────────────
# Базовые ответы
# ─────────────────────────────────────────────

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Обёртка для списочных ответов с пагинацией."""

    items: list[T]
    cursor: str | None = None
    has_more: bool = False
    total: int | None = None


class PeriodInfo(BaseModel):
    """Мета-информация о периоде в ответе."""

    start: date
    end: date
    days: int


# ─────────────────────────────────────────────
# Стандартные форматы числовых полей
# ─────────────────────────────────────────────

class AmountKZT(BaseModel):
    """Сумма в тенге с 2 знаками после запятой."""
    amount: Decimal = Field(..., decimal_places=2)


class PercentField(BaseModel):
    """Процентное значение с 4 знаками."""
    pct: Decimal = Field(..., decimal_places=4)


# ─────────────────────────────────────────────
# Коды бизнес-ошибок (из spec.md раздел 13.3)
# ─────────────────────────────────────────────

class BusinessError(Exception):
    """Базовое бизнес-исключение, конвертируемое в HTTP 400.

    Raises:
        Следует перехватывать в роутерах и конвертировать в HTTPException.
    """

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


# Предопределённые бизнес-ошибки
class InsufficientDataError(BusinessError):
    """Нет данных для расчёта показателя."""
    def __init__(self) -> None:
        super().__init__("INSUFFICIENT_DATA", "Insufficient data for calculation")


class SyncInProgressError(BusinessError):
    """Синхронизация МойСклад ещё выполняется."""
    def __init__(self) -> None:
        super().__init__("SYNC_IN_PROGRESS", "MoySklad sync is still in progress")


class ManualInputRequiredError(BusinessError):
    """Требуется ручной ввод данных (CAPEX, CAC)."""
    def __init__(self, field: str) -> None:
        super().__init__(
            "MANUAL_INPUT_REQUIRED",
            f"Manual input required for: {field}",
            {"field": field},
        )
