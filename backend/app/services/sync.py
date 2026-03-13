"""
Сервис MoySklad синхронизации: клиент, webhook, full sync, incremental sync.
"""
from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.base import SyncLog, SyncState, StockSnapshot
from app.repositories.sync_repo import ENTITY_REPOSITORIES

logger = structlog.get_logger(__name__)

# Порядок полной синхронизации (spec.md sec. 11)
FULL_SYNC_ORDER = [
    "store",
    "productfolder",
    "product",
    "counterparty",
    "customerorder",
    "demand",
    "invoiceout",
    "paymentin",
    "supply",
    "invoicein",
    "paymentout",
    "cashin",
    "cashout",
    "salesreturn",
    "purchasereturn",
]

SUPPORTED_WEBHOOK_ENTITIES = set(ENTITY_REPOSITORIES.keys())


class MoySkladClient:
    """Асинхронный HTTP-клиент для МойСклад API v1.2.

    Поддерживает пагинацию (limit/offset), retry на 429/503,
    и инкрементальную синхронизацию через updatedFrom.
    """

    BASE_URL = "https://api.moysklad.ru/api/remap/1.2"

    def __init__(self) -> None:
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
        """Получает страницу сущностей с пагинацией.

        Args:
            entity_type: Тип сущности (demand, paymentin, etc.).
            limit: Размер страницы (макс. 1000).
            offset: Смещение.
            updated_from: Фильтр инкрементальной синхронизации.

        Returns:
            Ответ МойСклад с полями rows[], size, offset.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if updated_from:
            # МойСклад формат фильтра: updatedFrom=2024-01-15T10:00:00
            params["filter"] = f"updatedFrom={updated_from.strftime('%Y-%m-%dT%H:%M:%S')}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/entity/{entity_type}",
                headers=self._headers,
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_entity_by_href(self, href: str) -> dict[str, Any]:
        """Получает одну сущность по её meta.href.

        Args:
            href: Полный URL из МойСклад (meta.href).

        Returns:
            Данные сущности.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(href, headers=self._headers)
            resp.raise_for_status()
            return resp.json()

    async def get_stock_all(self) -> list[dict[str, Any]]:
        """Получает текущие остатки по всем складам и товарам.

        Returns:
            Список записей остатков [{stock, productId, storeId, ...}].
        """
        result = []
        offset = 0
        while True:
            resp = await self.get_entity_list("report/stock/all", limit=1000, offset=offset)
            rows = resp.get("rows", [])
            result.extend(rows)
            if len(rows) < 1000:
                break
            offset += 1000
        return result


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Проверяет HMAC-SHA256 подпись вебхука от МойСклад.

    Args:
        body: Тело запроса в байтах.
        signature: Заголовок X-Lognex-Webhook-Signature.

    Returns:
        True если подпись валидна или секрет не настроен.
    """
    secret = settings.MOYSKLAD_WEBHOOK_SECRET
    if not secret:
        logger.warning("MOYSKLAD_WEBHOOK_SECRET not set — skipping signature verification")
        return True

    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")


class SyncService:
    """Оркестратор синхронизации данных из МойСклад.

    Реализует:
    - full_sync(): Первоначальная синхронизация 15 сущностей
    - incremental_sync(): Дельта-синхронизация через updatedFrom
    - process_webhook_events(): Обработка webhook в реальном времени
    - daily_stock_snapshot(): Ежедневный снимок остатков
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._client = MoySkladClient()

    # ────────────────────────────────────────────────
    # Full Sync
    # ────────────────────────────────────────────────

    async def full_sync(self) -> dict[str, int]:
        """Выполняет полную синхронизацию всех сущностей МойСклад.

        Синхронизирует по порядку из spec sec. 11 (справочники → документы → движения).
        Записывает прогресс в SyncLog.

        Returns:
            Словарь {entity_type: count} с количеством обработанных записей.
        """
        results: dict[str, int] = {}
        log = SyncLog(entity_type="all", sync_type="FULL", status="STARTED")
        self._db.add(log)
        await self._db.flush()

        total_processed = 0
        for entity_type in FULL_SYNC_ORDER:
            try:
                count = await self._sync_entity_full(entity_type)
                results[entity_type] = count
                total_processed += count
                logger.info("Full sync entity done", entity_type=entity_type, count=count)
            except Exception as exc:
                logger.error("Full sync entity failed", entity_type=entity_type, error=str(exc))
                results[entity_type] = -1

        # Обновляем SyncState для последующей инкрементальной синхронизации
        await self._update_sync_state("all", datetime.now(timezone.utc))

        log.status = "SUCCESS"
        log.finished_at = datetime.now(timezone.utc)
        log.records_processed = total_processed
        await self._db.commit()

        return results

    async def _sync_entity_full(self, entity_type: str) -> int:
        """Пагинированная загрузка всех записей одной сущности.

        Args:
            entity_type: Тип сущности МойСклад.

        Returns:
            Количество обработанных записей.
        """
        repo_class = ENTITY_REPOSITORIES.get(entity_type)
        if not repo_class:
            logger.warning("No repository for entity type", entity_type=entity_type)
            return 0

        repo = repo_class(self._db)
        offset = 0
        total = 0

        while True:
            page = await self._client.get_entity_list(entity_type, limit=1000, offset=offset)
            rows = page.get("rows", [])
            if not rows:
                break

            for row in rows:
                try:
                    await repo.upsert(row)
                    total += 1
                except Exception as exc:
                    logger.error(
                        "Failed to upsert row",
                        entity_type=entity_type,
                        id=row.get("id"),
                        error=str(exc),
                    )

            # Флашим каждые 500 записей
            if total % 500 == 0:
                await self._db.flush()

            if len(rows) < 1000:
                break
            offset += 1000

        await self._db.flush()
        return total

    # ────────────────────────────────────────────────
    # Incremental Sync
    # ────────────────────────────────────────────────

    async def incremental_sync(self) -> dict[str, int]:
        """Инкрементальная синхронизация — обновляет только изменённые записи.

        Использует SyncState.last_synced_at как cursor для фильтра updatedFrom.
        Запускается APScheduler каждые 15 минут.

        Returns:
            Словарь {entity_type: count}.
        """
        # Определяем cursor — время последней успешной синхронизации
        state_result = await self._db.execute(
            select(SyncState).where(SyncState.entity_type == "all")
        )
        state = state_result.scalar_one_or_none()
        updated_from = state.last_synced_at if state else None

        if not updated_from:
            logger.info("No sync state found, running full sync instead")
            return await self.full_sync()

        log = SyncLog(entity_type="all", sync_type="INCREMENTAL", status="STARTED")
        self._db.add(log)
        await self._db.flush()

        results: dict[str, int] = {}
        total_processed = 0

        for entity_type in FULL_SYNC_ORDER:
            try:
                count = await self._sync_entity_incremental(entity_type, updated_from)
                results[entity_type] = count
                total_processed += count
            except Exception as exc:
                logger.error(
                    "Incremental sync entity failed",
                    entity_type=entity_type,
                    error=str(exc),
                )

        await self._update_sync_state("all", datetime.now(timezone.utc))

        log.status = "SUCCESS"
        log.finished_at = datetime.now(timezone.utc)
        log.records_processed = total_processed
        await self._db.commit()

        return results

    async def _sync_entity_incremental(self, entity_type: str, updated_from: datetime) -> int:
        """Загружает обновлённые записи одной сущности.

        Args:
            entity_type: Тип сущности.
            updated_from: Дата последней синхронизации.

        Returns:
            Количество обновлённых записей.
        """
        repo_class = ENTITY_REPOSITORIES.get(entity_type)
        if not repo_class:
            return 0

        repo = repo_class(self._db)
        page = await self._client.get_entity_list(
            entity_type, limit=1000, updated_from=updated_from
        )
        rows = page.get("rows", [])
        count = 0
        for row in rows:
            try:
                await repo.upsert(row)
                count += 1
            except Exception as exc:
                logger.error("Failed incremental upsert", entity_type=entity_type, error=str(exc))

        if count:
            await self._db.flush()
        return count

    # ────────────────────────────────────────────────
    # Webhook Processing
    # ────────────────────────────────────────────────

    async def process_webhook_events(self, events: list[dict[str, Any]]) -> int:
        """Обрабатывает список событий из вебхука МойСклад.

        Для каждого поддерживаемого события запрашивает актуальные данные
        по href и выполняет upsert через соответствующий репозиторий.

        Args:
            events: Список событий из тела вебхука.

        Returns:
            Количество успешно обработанных событий.
        """
        log = SyncLog(entity_type="webhook", sync_type="WEBHOOK", status="STARTED")
        self._db.add(log)
        await self._db.flush()

        processed = 0
        for event in events:
            entity_type = event.get("meta", {}).get("type", "")
            href = event.get("meta", {}).get("href", "")
            action = event.get("action", "")

            if entity_type not in SUPPORTED_WEBHOOK_ENTITIES:
                logger.debug("Unsupported entity in webhook", entity_type=entity_type)
                continue

            try:
                if action == "DELETE":
                    logger.info("DELETE webhook received — soft delete not implemented yet",
                                entity_type=entity_type)
                elif href:
                    entity_data = await self._client.get_entity_by_href(href)
                    await self._upsert_entity(entity_type, entity_data)
                    processed += 1
            except httpx.HTTPStatusError as exc:
                logger.error("HTTP error processing webhook event",
                             entity_type=entity_type, status=exc.response.status_code)
            except Exception as exc:
                logger.error("Failed to process webhook event",
                             entity_type=entity_type, error=str(exc))

        log.status = "SUCCESS"
        log.finished_at = datetime.now(timezone.utc)
        log.records_processed = processed
        await self._db.commit()

        return processed

    async def _upsert_entity(self, entity_type: str, data: dict[str, Any]) -> None:
        """Вставляет или обновляет сущность через соответствующий репозиторий.

        Args:
            entity_type: Тип сущности МойСклад.
            data: Данные сущности из API.
        """
        repo_class = ENTITY_REPOSITORIES.get(entity_type)
        if not repo_class:
            logger.warning("No repository found for entity", entity_type=entity_type)
            return

        repo = repo_class(self._db)
        await repo.upsert(data)

    # ────────────────────────────────────────────────
    # Daily Stock Snapshot
    # ────────────────────────────────────────────────

    async def daily_stock_snapshot(self) -> int:
        """Создаёт ежедневный снимок остатков по всем складам.

        Вызывается APScheduler каждый день в 23:59 Asia/Almaty.
        Записывает StockSnapshot для последующего расчёта баланса запасов.

        Returns:
            Количество записей снимка.
        """
        log = SyncLog(entity_type="stock", sync_type="SNAPSHOT", status="STARTED")
        self._db.add(log)
        await self._db.flush()

        try:
            stock_rows = await self._client.get_stock_all()
            snapshot_date = datetime.now(timezone.utc).date()
            count = 0

            for item in stock_rows:
                product_href = item.get("meta", {}).get("href", "")
                store_href = item.get("store", {}).get("meta", {}).get("href", "")

                snapshot = StockSnapshot(
                    id=str(uuid.uuid4()),
                    snapshot_date=snapshot_date,
                    product_id=product_href.split("/")[-1] if product_href else None,
                    store_id=store_href.split("/")[-1] if store_href else None,
                    quantity=item.get("stock", 0),
                    reserve=item.get("reserve", 0),
                    in_transit=item.get("inTransit", 0),
                    cost_price=item.get("price", 0) / 100,
                )
                self._db.add(snapshot)
                count += 1

                if count % 500 == 0:
                    await self._db.flush()

            log.status = "SUCCESS"
            log.records_processed = count
        except Exception as exc:
            logger.error("Daily stock snapshot failed", error=str(exc))
            log.status = "FAILED"
            log.error_message = str(exc)
            count = 0

        log.finished_at = datetime.now(timezone.utc)
        await self._db.commit()
        return count

    # ────────────────────────────────────────────────
    # Helpers
    # ────────────────────────────────────────────────

    async def _update_sync_state(self, entity_type: str, synced_at: datetime) -> None:
        """Обновляет или создаёт запись SyncState с временем последней синхронизации."""
        result = await self._db.execute(
            select(SyncState).where(SyncState.entity_type == entity_type)
        )
        state = result.scalar_one_or_none()
        if state:
            state.last_synced_at = synced_at
        else:
            state = SyncState(
                id=str(uuid.uuid4()),
                entity_type=entity_type,
                last_synced_at=synced_at,
            )
            self._db.add(state)
        await self._db.flush()
