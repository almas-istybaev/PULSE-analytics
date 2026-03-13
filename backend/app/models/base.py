"""
SQLAlchemy ORM модели для всех синхронизируемых сущностей МойСклад.

Все модели содержат общие поля: moysklad_id, moysklad_href, synced_at.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer, Numeric,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей Pulse.

    Предоставляет общие поля: created_at, updated_at.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class MoySkladMixin:
    """Миксин для всех моделей, синхронизированных из МойСклад.

    Предоставляет moysklad_id (уникальный), moysklad_href и synced_at.
    """

    moysklad_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    moysklad_href: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    moysklad_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="updatedAt из МойСклад"
    )


# ─────────────────────────────────────────────
# Справочники
# ─────────────────────────────────────────────

class Store(Base, MoySkladMixin):
    """Склад / магазин из МойСклад (store)."""

    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ProductFolder(Base, MoySkladMixin):
    """Группа / категория товаров из МойСклад (productfolder)."""

    __tablename__ = "product_folders"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path_name: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("product_folders.id"), nullable=True)

    products: Mapped[list["Product"]] = relationship("Product", back_populates="folder")


class Product(Base, MoySkladMixin):
    """Товар из МойСклад (product)."""

    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_folder_id", "folder_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    article: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    buy_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True, comment="Закупочная цена")
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True, comment="Цена продажи")
    folder_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("product_folders.id"), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    folder: Mapped["ProductFolder | None"] = relationship("ProductFolder", back_populates="products")


class Counterparty(Base, MoySkladMixin):
    """Контрагент (клиент или поставщик) из МойСклад (counterparty)."""

    __tablename__ = "counterparties"
    __table_args__ = (
        Index("ix_counterparties_type", "counterparty_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    inn: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="ИИН/БИН")
    phone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counterparty_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="customer | supplier | both"
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


# ─────────────────────────────────────────────
# Документы МойСклад
# ─────────────────────────────────────────────

class CustomerOrder(Base, MoySkladMixin):
    """Заказ покупателя (customerorder)."""

    __tablename__ = "customer_orders"
    __table_args__ = (
        Index("ix_customer_orders_moment", "moment"),
        Index("ix_customer_orders_counterparty", "counterparty_id"),
        Index("ix_customer_orders_store_moment", "store_id", "moment"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="Дата заказа")
    delivery_planned_moment: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Планируемая дата отгрузки"
    )
    sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    store_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stores.id"), nullable=True)
    counterparty_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("counterparties.id"), nullable=True)


class Demand(Base, MoySkladMixin):
    """Отгрузка / реализация (demand)."""

    __tablename__ = "demands"
    __table_args__ = (
        Index("ix_demands_moment", "moment"),
        Index("ix_demands_store_moment", "store_id", "moment"),
        Index("ix_demands_counterparty", "counterparty_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True, comment="Сумма отгрузки")
    cogs_sum: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True, comment="Себестоимость (buyPrice × quantity)"
    )
    store_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stores.id"), nullable=True)
    counterparty_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("counterparties.id"), nullable=True)
    customer_order_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="Связанный заказ")


class Supply(Base, MoySkladMixin):
    """Поставка (supply)."""

    __tablename__ = "supplies"
    __table_args__ = (
        Index("ix_supplies_moment", "moment"),
        Index("ix_supplies_counterparty", "counterparty_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    store_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stores.id"), nullable=True)
    counterparty_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("counterparties.id"), nullable=True)


class SalesReturn(Base, MoySkladMixin):
    """Возврат от покупателя (salesreturn)."""

    __tablename__ = "sales_returns"
    __table_args__ = (Index("ix_sales_returns_moment", "moment"),)

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    store_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stores.id"), nullable=True)
    counterparty_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("counterparties.id"), nullable=True)
    demand_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="Связанная отгрузка")


class PurchaseReturn(Base, MoySkladMixin):
    """Возврат поставщику (purchasereturn)."""

    __tablename__ = "purchase_returns"
    __table_args__ = (Index("ix_purchase_returns_moment", "moment"),)

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    store_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stores.id"), nullable=True)
    counterparty_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("counterparties.id"), nullable=True)


class InvoiceOut(Base, MoySkladMixin):
    """Счёт покупателю (invoiceout)."""

    __tablename__ = "invoices_out"
    __table_args__ = (
        Index("ix_invoices_out_paid_moment", "is_paid", "moment"),
        Index("ix_invoices_out_counterparty", "counterparty_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    paid_sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    counterparty_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("counterparties.id"), nullable=True)


class InvoiceIn(Base, MoySkladMixin):
    """Счёт поставщика (invoicein)."""

    __tablename__ = "invoices_in"
    __table_args__ = (
        Index("ix_invoices_in_paid_moment", "is_paid", "moment"),
        Index("ix_invoices_in_counterparty", "counterparty_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    paid_sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    counterparty_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("counterparties.id"), nullable=True)


class PaymentIn(Base, MoySkladMixin):
    """Входящий платёж / оплата от покупателя (paymentin)."""

    __tablename__ = "payments_in"
    __table_args__ = (
        Index("ix_payments_in_moment", "moment"),
        Index("ix_payments_in_counterparty", "counterparty_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Назначение платежа")
    counterparty_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("counterparties.id"), nullable=True)
    invoice_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="Связанный счёт")


class PaymentOut(Base, MoySkladMixin):
    """Исходящий платёж / оплата поставщику (paymentout)."""

    __tablename__ = "payments_out"
    __table_args__ = (
        Index("ix_payments_out_moment", "moment"),
        Index("ix_payments_out_counterparty", "counterparty_id"),
        Index("ix_payments_out_expense_type", "expense_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    expense_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="CAPEX | OPEX | DIVIDENDS | LOAN"
    )
    counterparty_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("counterparties.id"), nullable=True)


class CashIn(Base, MoySkladMixin):
    """Приходный кассовый ордер (cashin)."""

    __tablename__ = "cash_ins"
    __table_args__ = (Index("ix_cash_ins_moment", "moment"),)

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)


class CashOut(Base, MoySkladMixin):
    """Расходный кассовый ордер (cashout)."""

    __tablename__ = "cash_outs"
    __table_args__ = (Index("ix_cash_outs_moment", "moment"),)

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sum: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)


# ─────────────────────────────────────────────
# Системные таблицы
# ─────────────────────────────────────────────

class StockSnapshot(Base):
    """Ежедневный снимок остатков товаров по складам.

    Заполняется cron-задачей в 23:59 каждый день.
    Используется для расчёта средних запасов в GMROI, DIO, Балансе.
    """

    __tablename__ = "stock_snapshots"
    __table_args__ = (
        Index("ix_stock_snapshots_date_product", "snapshot_date", "product_id"),
        Index("ix_stock_snapshots_date_store", "snapshot_date", "store_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False)
    store_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stores.id"), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    buy_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    value: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True, comment="quantity × buy_price"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SyncLog(Base):
    """Лог синхронизаций с МойСклад.

    Отслеживает статус, время и ошибки каждой операции синхронизации.
    """

    __tablename__ = "sync_logs"
    __table_args__ = (
        Index("ix_sync_logs_entity_type", "entity_type"),
        Index("ix_sync_logs_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="Тип сущности МойСклад")
    sync_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="FULL | INCREMENTAL | WEBHOOK"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="STARTED", comment="STARTED | SUCCESS | FAILED"
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SyncState(Base):
    """Курсоры инкрементальной синхронизации (updatedFrom per entity type)."""

    __tablename__ = "sync_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ManualInput(Base):
    """Ручной ввод данных: CAPEX, CAC, амортизация.

    Используется для показателей, недоступных из МойСклад напрямую.
    Например: маркетинговые расходы для расчёта CAC.
    """

    __tablename__ = "manual_inputs"
    __table_args__ = (
        Index("ix_manual_inputs_type_period", "input_type", "period"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    input_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="CAPEX | CAC | DEPRECIATION | DIVIDEND | LOAN_PAYMENT | OTHER"
    )
    period: Mapped[str] = mapped_column(String(7), nullable=False, comment="Период YYYY-MM")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Подкатегория")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="Канал (для CAC)")


class User(Base):
    """Пользователь системы Pulse с ролевым доступом (RBAC)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="cfo",
        comment="admin | ceo | cfo | cco | buyer | investor"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
