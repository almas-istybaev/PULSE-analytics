"""
Конкретные репозитории для каждой сущности МойСклад.

Каждый репозиторий реализует метод upsert(data),
который принимает JSON-ответ МойСклад и записывает/обновляет
соответствующую SQLAlchemy-модель.
"""
from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import (
    CashIn,
    CashOut,
    Counterparty,
    CustomerOrder,
    Demand,
    InvoiceIn,
    InvoiceOut,
    PaymentIn,
    PaymentOut,
    Product,
    ProductFolder,
    PurchaseReturn,
    SalesReturn,
    Store,
    Supply,
)
from app.repositories.base import (
    BaseRepository,
    _extract_id,
    _parse_datetime,
    _sum_to_decimal,
)

logger = structlog.get_logger(__name__)


class StoreRepository(BaseRepository):
    """Репозиторий складов."""

    async def upsert(self, data: dict[str, Any]) -> None:
        href = data.get("meta", {}).get("href", "")
        await self._merge(Store, data["id"], {
            "moysklad_href": href,
            "name": data.get("name", ""),
            "description": data.get("description"),
            "address": data.get("address"),
            "is_active": not data.get("archived", False),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class ProductFolderRepository(BaseRepository):
    """Репозиторий категорий товаров."""

    async def upsert(self, data: dict[str, Any]) -> None:
        await self._merge(ProductFolder, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "description": data.get("description"),
            "parent_id": _extract_id(
                data.get("productFolder", {}).get("meta", {}).get("href")
            ),
            "is_active": not data.get("archived", False),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class ProductRepository(BaseRepository):
    """Репозиторий товаров."""

    async def upsert(self, data: dict[str, Any]) -> None:
        buy_price = _sum_to_decimal(
            data.get("buyPrice", {}).get("value")
        )
        sale_price = None
        sale_prices = data.get("salePrices", [])
        if sale_prices:
            sale_price = _sum_to_decimal(sale_prices[0].get("value"))

        await self._merge(Product, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "article": data.get("article"),
            "code": data.get("code"),
            "description": data.get("description"),
            "buy_price": buy_price,
            "sale_price": sale_price,
            "folder_id": _extract_id(
                data.get("productFolder", {}).get("meta", {}).get("href")
            ),
            "is_active": not data.get("archived", False),
            "weight": data.get("weight"),
            "volume": data.get("volume"),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class CounterpartyRepository(BaseRepository):
    """Репозиторий контрагентов (клиенты и поставщики)."""

    async def upsert(self, data: dict[str, Any]) -> None:
        await self._merge(Counterparty, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "company_type": data.get("companyType"),
            "phone": data.get("phone"),
            "email": data.get("email"),
            "inn": data.get("inn"),
            "kpp": data.get("kpp"),
            "is_active": not data.get("archived", False),
            "first_demand_date": _parse_datetime(data.get("firstDemandDate")),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class CustomerOrderRepository(BaseRepository):
    """Репозиторий заказов покупателей."""

    async def upsert(self, data: dict[str, Any]) -> None:
        await self._merge(CustomerOrder, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "moment": _parse_datetime(data.get("moment")),
            "sum": _sum_to_decimal(data.get("sum")),
            "counterparty_id": _extract_id(
                data.get("agent", {}).get("meta", {}).get("href")
            ),
            "store_id": _extract_id(
                data.get("store", {}).get("meta", {}).get("href")
            ),
            "status": data.get("state", {}).get("name"),
            "delivery_planned_moment": _parse_datetime(data.get("deliveryPlannedMoment")),
            "shipped_sum": _sum_to_decimal(data.get("shippedSum")),
            "invoice_out_sum": _sum_to_decimal(data.get("invoicedSum")),
            "is_paid": (data.get("shippedSum", 0) or 0) >= (data.get("sum", 0) or 0),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class DemandRepository(BaseRepository):
    """Репозиторий отгрузок."""

    async def upsert(self, data: dict[str, Any]) -> None:
        await self._merge(Demand, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "moment": _parse_datetime(data.get("moment")),
            "sum": _sum_to_decimal(data.get("sum")),
            "counterparty_id": _extract_id(
                data.get("agent", {}).get("meta", {}).get("href")
            ),
            "store_id": _extract_id(
                data.get("store", {}).get("meta", {}).get("href")
            ),
            "customer_order_id": _extract_id(
                data.get("customerOrder", {}).get("meta", {}).get("href")
            ),
            "cost_sum": _sum_to_decimal(data.get("costSum")),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class SupplyRepository(BaseRepository):
    """Репозиторий поставок."""

    async def upsert(self, data: dict[str, Any]) -> None:
        await self._merge(Supply, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "moment": _parse_datetime(data.get("moment")),
            "sum": _sum_to_decimal(data.get("sum")),
            "counterparty_id": _extract_id(
                data.get("agent", {}).get("meta", {}).get("href")
            ),
            "store_id": _extract_id(
                data.get("store", {}).get("meta", {}).get("href")
            ),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class SalesReturnRepository(BaseRepository):
    """Репозиторий возвратов от покупателей."""

    async def upsert(self, data: dict[str, Any]) -> None:
        await self._merge(SalesReturn, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "moment": _parse_datetime(data.get("moment")),
            "sum": _sum_to_decimal(data.get("sum")),
            "counterparty_id": _extract_id(
                data.get("agent", {}).get("meta", {}).get("href")
            ),
            "store_id": _extract_id(
                data.get("store", {}).get("meta", {}).get("href")
            ),
            "demand_id": _extract_id(
                data.get("demand", {}).get("meta", {}).get("href")
            ),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class PurchaseReturnRepository(BaseRepository):
    """Репозиторий возвратов поставщикам."""

    async def upsert(self, data: dict[str, Any]) -> None:
        await self._merge(PurchaseReturn, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "moment": _parse_datetime(data.get("moment")),
            "sum": _sum_to_decimal(data.get("sum")),
            "counterparty_id": _extract_id(
                data.get("agent", {}).get("meta", {}).get("href")
            ),
            "store_id": _extract_id(
                data.get("store", {}).get("meta", {}).get("href")
            ),
            "supply_id": _extract_id(
                data.get("supply", {}).get("meta", {}).get("href")
            ),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class InvoiceOutRepository(BaseRepository):
    """Репозиторий счетов покупателям."""

    async def upsert(self, data: dict[str, Any]) -> None:
        paid_sum = _sum_to_decimal(data.get("payedSum"))
        total_sum = _sum_to_decimal(data.get("sum"))
        await self._merge(InvoiceOut, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "moment": _parse_datetime(data.get("moment")),
            "sum": total_sum,
            "counterparty_id": _extract_id(
                data.get("agent", {}).get("meta", {}).get("href")
            ),
            "customer_order_id": _extract_id(
                data.get("customerOrder", {}).get("meta", {}).get("href")
            ),
            "paid_sum": paid_sum,
            "is_paid": paid_sum >= total_sum if total_sum > 0 else False,
            "due_date": _parse_datetime(data.get("paymentPlannedMoment")),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class InvoiceInRepository(BaseRepository):
    """Репозиторий счетов от поставщиков."""

    async def upsert(self, data: dict[str, Any]) -> None:
        paid_sum = _sum_to_decimal(data.get("payedSum"))
        total_sum = _sum_to_decimal(data.get("sum"))
        await self._merge(InvoiceIn, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "moment": _parse_datetime(data.get("moment")),
            "sum": total_sum,
            "counterparty_id": _extract_id(
                data.get("agent", {}).get("meta", {}).get("href")
            ),
            "supply_id": _extract_id(
                data.get("supply", {}).get("meta", {}).get("href")
            ),
            "paid_sum": paid_sum,
            "is_paid": paid_sum >= total_sum if total_sum > 0 else False,
            "due_date": _parse_datetime(data.get("paymentPlannedMoment")),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class PaymentInRepository(BaseRepository):
    """Репозиторий входящих платежей."""

    async def upsert(self, data: dict[str, Any]) -> None:
        await self._merge(PaymentIn, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "moment": _parse_datetime(data.get("moment")),
            "sum": _sum_to_decimal(data.get("sum")),
            "counterparty_id": _extract_id(
                data.get("agent", {}).get("meta", {}).get("href")
            ),
            "purpose": data.get("paymentPurpose"),
            "income_type": data.get("incomingType"),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class PaymentOutRepository(BaseRepository):
    """Репозиторий исходящих платежей."""

    async def upsert(self, data: dict[str, Any]) -> None:
        # Определяем тип расхода по категории (expense_type)
        expense_type = _classify_expense(data)
        await self._merge(PaymentOut, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "moment": _parse_datetime(data.get("moment")),
            "sum": _sum_to_decimal(data.get("sum")),
            "counterparty_id": _extract_id(
                data.get("agent", {}).get("meta", {}).get("href")
            ),
            "purpose": data.get("paymentPurpose"),
            "expense_type": expense_type,
            "updated_at": _parse_datetime(data.get("updated")),
        })


class CashInRepository(BaseRepository):
    """Репозиторий приходных кассовых ордеров."""

    async def upsert(self, data: dict[str, Any]) -> None:
        await self._merge(CashIn, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "moment": _parse_datetime(data.get("moment")),
            "sum": _sum_to_decimal(data.get("sum")),
            "counterparty_id": _extract_id(
                data.get("agent", {}).get("meta", {}).get("href")
            ),
            "purpose": data.get("paymentPurpose"),
            "updated_at": _parse_datetime(data.get("updated")),
        })


class CashOutRepository(BaseRepository):
    """Репозиторий расходных кассовых ордеров."""

    async def upsert(self, data: dict[str, Any]) -> None:
        await self._merge(CashOut, data["id"], {
            "moysklad_href": data.get("meta", {}).get("href", ""),
            "name": data.get("name", ""),
            "moment": _parse_datetime(data.get("moment")),
            "sum": _sum_to_decimal(data.get("sum")),
            "counterparty_id": _extract_id(
                data.get("agent", {}).get("meta", {}).get("href")
            ),
            "purpose": data.get("paymentPurpose"),
            "expense_type": _classify_expense(data),
            "updated_at": _parse_datetime(data.get("updated")),
        })


# ──────────────────────────────────────────────────────
# Утилиты
# ──────────────────────────────────────────────────────

def _classify_expense(data: dict[str, Any]) -> str:
    """Классифицирует исходящий платёж по назначению.

    Проверяет name и paymentPurpose на ключевые слова для определения
    типа расхода: OPEX / CAPEX / DIVIDEND / LOAN / TAX.

    Args:
        data: Данные платёжного документа из МойСклад.

    Returns:
        Строка-тип расхода.
    """
    text = " ".join(filter(None, [
        data.get("name", ""),
        data.get("paymentPurpose", ""),
    ])).lower()

    if any(kw in text for kw in ("дивиденд", "dividend")):
        return "DIVIDEND"
    if any(kw in text for kw in ("капекс", "capex", "оборудовани", "основн", "недвижим")):
        return "CAPEX"
    if any(kw in text for kw in ("налог", "ндс", "кпн", "tax")):
        return "TAX"
    if any(kw in text for kw in ("кредит", "займ", "loan", "погашени")):
        return "LOAN"
    return "OPEX"


# ──────────────────────────────────────────────────────
# Реестр репозиториев: entity_type → класс
# ──────────────────────────────────────────────────────

ENTITY_REPOSITORIES: dict[str, type[BaseRepository]] = {
    "store":           StoreRepository,
    "productfolder":   ProductFolderRepository,
    "product":         ProductRepository,
    "counterparty":    CounterpartyRepository,
    "customerorder":   CustomerOrderRepository,
    "demand":          DemandRepository,
    "supply":          SupplyRepository,
    "salesreturn":     SalesReturnRepository,
    "purchasereturn":  PurchaseReturnRepository,
    "invoiceout":      InvoiceOutRepository,
    "invoicein":       InvoiceInRepository,
    "paymentin":       PaymentInRepository,
    "paymentout":      PaymentOutRepository,
    "cashin":          CashInRepository,
    "cashout":         CashOutRepository,
}
