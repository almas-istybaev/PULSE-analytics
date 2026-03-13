"""
Базовый репозиторий для работы с МойСклад сущностями.
"""
from __future__ import annotations

from typing import Any, TypeVar

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ModelT = TypeVar("ModelT")


def _extract_id(href: str | None) -> str | None:
    """Извлекает ID из meta.href МойСклад.

    Args:
        href: Полный URL вида https://api.moysklad.ru/api/remap/1.2/entity/product/{uuid}

    Returns:
        UUID строкой или None.
    """
    if not href:
        return None
    parts = href.rstrip("/").split("/")
    return parts[-1] if parts else None


def _parse_datetime(value: str | None):
    """Парсит дату из формата МойСклад (ISO 8601 с миллисекундами)."""
    if not value:
        return None
    from datetime import datetime
    try:
        # МойСклад формат: "2024-01-15 12:30:00.000"
        return datetime.fromisoformat(value.replace(" ", "T").replace(".000", ""))
    except (ValueError, TypeError):
        return None


def _sum_to_decimal(value: int | None):
    """Конвертирует сумму МойСклад (в копейках × 100) в Decimal KZT.

    МойСклад хранит суммы в минимальных единицах (копейки = / 100).
    """
    from decimal import Decimal
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)) / Decimal("100")


class BaseRepository:
    """Базовый репозиторий с UPSERT-логикой для сущностей МойСклад.

    Все конкретные репозитории наследуют этот класс и реализуют
    метод `_build_model(data)` для маппинга полей.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert(self, data: dict[str, Any]) -> None:
        """Вставляет или обновляет запись по moysklad_id.

        Args:
            data: Словарь данных сущности из МойСклад API.
        """
        raise NotImplementedError

    async def _merge(self, model_class: type, moysklad_id: str, fields: dict[str, Any]) -> None:
        """Выполняет upsert через SQLAlchemy merge/select+update паттерн.

        Args:
            model_class: Класс SQLAlchemy модели.
            moysklad_id: ID сущности в МойСклад.
            fields: Словарь значений полей для обновления.
        """
        from datetime import datetime, timezone
        from sqlalchemy import update

        result = await self._db.execute(
            select(model_class).where(model_class.moysklad_id == moysklad_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Обновляем существующую запись
            await self._db.execute(
                update(model_class)
                .where(model_class.moysklad_id == moysklad_id)
                .values(**fields, synced_at=datetime.now(timezone.utc))
            )
        else:
            # Создаём новую запись
            import uuid
            obj = model_class(
                id=str(uuid.uuid4()),
                moysklad_id=moysklad_id,
                synced_at=datetime.now(timezone.utc),
                **fields,
            )
            self._db.add(obj)
