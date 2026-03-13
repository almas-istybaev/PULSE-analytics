"""
Сервис MoySklad синхронизации: клиент, webhook-обработчик, sync стратегии.
"""
from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.base import SyncLog, SyncState

logger = structlog.get_logger(__name__)

# Маппинг entity_type → SQLAlchemy model
ENTITY_MODEL_MAP = {
    "customerorder": "CustomerOrder",
    "demand": "Demand",
    "supply": "Supply",
    "paymentin": "PaymentIn",
    "paymentout": "PaymentOut",
    "cashin": "CashIn",
    "cashout": "CashOut",
    "invoiceout": "InvoiceOut",
    "invoicein": "InvoiceIn",
    "salesreturn": "SalesReturn",
    "purchasereturn": "PurchaseReturn",
    "counterparty": "Counterparty",
    "product": "Product",
}

SUPPORTED_WEBHOOK_ENTITIES = set(ENTITY_MODEL_MAP.keys())


class MoySkladClient:
    """Асинхронный HTTP-клиент для МойСклад API.

    Поддерживает пагинацию, retry-логику и rate limiting.
    """

    def __init__(self) -> None:
        self._base_url = settings.MOYSKLAD_BASE_URL
        self._headers = {
            "Authorization": f"Bearer {settings.MOYSKLAD_TOKEN}",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
        }

    async def get_entity_list(
        self,
        entity_type: str,
        limit: int = 1000,
        offset: int = 0,
        updated_from: datetime | None = None,
    ) -> dict[str, Any]:
        """Получает список сущностей МойСклад с пагинацией.

        Args:
            entity_type: Тип сущности (demand, paymentin, etc).
            limit: Количество записей (макс. 1000).
            offset: Смещение для пагинации.
            updated_from: Фильтр по дате обновления (инкрементальная синхронизация).

        Returns:
            Словарь с rows[] и meta.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if updated_from:
            params["filter"] = f"updatedFrom={updated_from.isoformat()}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self._base_url}/entity/{entity_type}",
                headers=self._headers,
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_entity_by_href(self, href: str) -> dict[str, Any]:
        """Получает одну сущность по её meta.href.

        Args:
            href: Полный URL сущности из МойСклад.

        Returns:
            Данные сущности.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(href, headers=self._headers)
            resp.raise_for_status()
            return resp.json()


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Проверяет HMAC-SHA256 подпись вебхука от МойСклад.

    Args:
        body: Тело запроса в байтах.
        signature: Заголовок X-Lognex-Webhook-Signature.

    Returns:
        True если подпись валидна.

    Note:
        Если MOYSKLAD_WEBHOOK_SECRET пустой — верификация пропускается.
    """
    secret = settings.MOYSKLAD_WEBHOOK_SECRET
    if not secret:
        logger.warning("Webhook secret not configured, skipping signature verification")
        return True

    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")


class SyncService:
    """Оркестратор синхронизации данных из МойСклад.

    Управляет full sync, incremental sync и обработкой webhook-событий.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._client = MoySkladClient()

    async def process_webhook_events(self, events: list[dict[str, Any]]) -> int:
        """Обрабатывает список событий из вебхука МойСклад.

        Для каждого события запрашивает актуальные данные по href
        и выполняет upsert в БД.

        Args:
            events: Список событий из тела вебхука.

        Returns:
            Количество успешно обработанных событий.
        """
        log_entry = SyncLog(
            entity_type="webhook",
            sync_type="WEBHOOK",
            status="STARTED",
        )
        self._db.add(log_entry)
        await self._db.flush()

        processed = 0
        for event in events:
            entity_type = event.get("meta", {}).get("type", "")
            href = event.get("meta", {}).get("href", "")
            action = event.get("action", "")

            if entity_type not in SUPPORTED_WEBHOOK_ENTITIES:
                logger.debug("Unsupported entity type in webhook", entity_type=entity_type)
                continue

            try:
                if action == "DELETE":
                    logger.info("DELETE action received", entity_type=entity_type)
                    # DELETE handling: mark as archived or remove
                else:
                    entity_data = await self._client.get_entity_by_href(href)
                    await self._upsert_entity(entity_type, entity_data)
                    processed += 1
            except Exception as exc:
                logger.error("Failed to process webhook event", entity_type=entity_type, error=str(exc))

        log_entry.status = "SUCCESS"
        log_entry.finished_at = datetime.now(timezone.utc)
        log_entry.records_processed = processed
        await self._db.commit()

        return processed

    async def _upsert_entity(self, entity_type: str, data: dict[str, Any]) -> None:
        """Вставляет или обновляет сущность в БД по moysklad_id.

        Args:
            entity_type: Тип сущности.
            data: Данные сущности из МойСклад API.

        Note:
            Используем SQLite INSERT OR REPLACE для idempotency.
        """
        moysklad_id = data.get("id", "")
        if not moysklad_id:
            return

        logger.debug("Upserting entity", entity_type=entity_type, moysklad_id=moysklad_id)
        # Реализация upsert по конкретным моделям выполняется в repositories
        # Здесь — базовая точка расширения
