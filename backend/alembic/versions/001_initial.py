"""Initial migration — создание всех таблиц Pulse.

Revision ID: 001
Revises:
Create Date: 2026-03-13
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создаёт все таблицы и индексы."""

    # ─── Справочники ────────────────────────────────────
    op.create_table(
        "stores",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("moysklad_id", sa.String(36), nullable=False, unique=True, index=True),
        sa.Column("moysklad_href", sa.String(500)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("address", sa.String(500)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("synced_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "product_folders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("moysklad_id", sa.String(36), nullable=False, unique=True, index=True),
        sa.Column("moysklad_href", sa.String(500)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("synced_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("moysklad_id", sa.String(36), nullable=False, unique=True, index=True),
        sa.Column("moysklad_href", sa.String(500)),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("article", sa.String(255)),
        sa.Column("code", sa.String(255)),
        sa.Column("description", sa.Text),
        sa.Column("buy_price", sa.Numeric(18, 2), default=0),
        sa.Column("sale_price", sa.Numeric(18, 2)),
        sa.Column("folder_id", sa.String(36), nullable=True),
        sa.Column("weight", sa.Float),
        sa.Column("volume", sa.Float),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("synced_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "counterparties",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("moysklad_id", sa.String(36), nullable=False, unique=True, index=True),
        sa.Column("moysklad_href", sa.String(500)),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("company_type", sa.String(50)),
        sa.Column("phone", sa.String(100)),
        sa.Column("email", sa.String(255)),
        sa.Column("inn", sa.String(50)),
        sa.Column("kpp", sa.String(50)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("first_demand_date", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("synced_at", sa.DateTime(timezone=True)),
    )

    # ─── Документы ────────────────────────────────────
    _doc_columns = [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("moysklad_id", sa.String(36), nullable=False, unique=True),
        sa.Column("moysklad_href", sa.String(500)),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("moment", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sum", sa.Numeric(18, 2), default=0),
        sa.Column("counterparty_id", sa.String(36)),
        sa.Column("store_id", sa.String(36)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("synced_at", sa.DateTime(timezone=True)),
    ]

    op.create_table(
        "customer_orders",
        *_doc_columns,
        sa.Column("status", sa.String(100)),
        sa.Column("delivery_planned_moment", sa.DateTime(timezone=True)),
        sa.Column("shipped_sum", sa.Numeric(18, 2), default=0),
        sa.Column("invoice_out_sum", sa.Numeric(18, 2), default=0),
        sa.Column("is_paid", sa.Boolean, default=False),
    )
    op.create_index("ix_customer_orders_moment", "customer_orders", ["moment"])
    op.create_index("ix_customer_orders_cp_moment", "customer_orders", ["counterparty_id", "moment"])

    op.create_table(
        "demands",
        *_doc_columns,
        sa.Column("customer_order_id", sa.String(36)),
        sa.Column("cost_sum", sa.Numeric(18, 2), default=0),
    )
    op.create_index("ix_demands_moment", "demands", ["moment"])

    op.create_table(
        "supplies",
        *_doc_columns,
    )
    op.create_index("ix_supplies_moment", "supplies", ["moment"])

    op.create_table(
        "sales_returns",
        *_doc_columns,
        sa.Column("demand_id", sa.String(36)),
    )
    op.create_index("ix_sales_returns_moment", "sales_returns", ["moment"])

    op.create_table(
        "purchase_returns",
        *_doc_columns,
        sa.Column("supply_id", sa.String(36)),
    )
    op.create_index("ix_purchase_returns_moment", "purchase_returns", ["moment"])

    # ─── Счета ────────────────────────────────────────
    op.create_table(
        "invoice_outs",
        *_doc_columns,
        sa.Column("customer_order_id", sa.String(36)),
        sa.Column("paid_sum", sa.Numeric(18, 2), default=0),
        sa.Column("is_paid", sa.Boolean, default=False),
        sa.Column("due_date", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_invoice_outs_moment", "invoice_outs", ["moment"])
    op.create_index("ix_invoice_outs_cp_moment", "invoice_outs", ["counterparty_id", "moment"])

    op.create_table(
        "invoice_ins",
        *_doc_columns,
        sa.Column("supply_id", sa.String(36)),
        sa.Column("paid_sum", sa.Numeric(18, 2), default=0),
        sa.Column("is_paid", sa.Boolean, default=False),
        sa.Column("due_date", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_invoice_ins_moment", "invoice_ins", ["moment"])

    # ─── Платежи ──────────────────────────────────────
    op.create_table(
        "payment_ins",
        *_doc_columns,
        sa.Column("purpose", sa.Text),
        sa.Column("income_type", sa.String(100)),
    )
    op.create_index("ix_payment_ins_moment", "payment_ins", ["moment"])

    op.create_table(
        "payment_outs",
        *_doc_columns,
        sa.Column("purpose", sa.Text),
        sa.Column("expense_type", sa.String(50), default="OPEX"),
    )
    op.create_index("ix_payment_outs_moment", "payment_outs", ["moment"])

    op.create_table(
        "cash_ins",
        *_doc_columns,
        sa.Column("purpose", sa.Text),
    )
    op.create_index("ix_cash_ins_moment", "cash_ins", ["moment"])

    op.create_table(
        "cash_outs",
        *_doc_columns,
        sa.Column("purpose", sa.Text),
        sa.Column("expense_type", sa.String(50), default="OPEX"),
    )
    op.create_index("ix_cash_outs_moment", "cash_outs", ["moment"])

    # ─── Системные таблицы ────────────────────────────
    op.create_table(
        "stock_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("product_id", sa.String(36)),
        sa.Column("store_id", sa.String(36)),
        sa.Column("quantity", sa.Float, default=0),
        sa.Column("reserve", sa.Float, default=0),
        sa.Column("in_transit", sa.Float, default=0),
        sa.Column("cost_price", sa.Numeric(18, 2), default=0),
    )
    op.create_index(
        "ix_stock_snapshots_date_product",
        "stock_snapshots",
        ["snapshot_date", "product_id"],
    )

    op.create_table(
        "sync_logs",
        sa.Column("id", sa.String(36), primary_key=True, default=lambda: __import__("uuid").uuid4().hex),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("sync_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("records_processed", sa.Integer, default=0),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "sync_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(100), nullable=False, unique=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "manual_inputs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("metric_key", sa.String(100), nullable=False),
        sa.Column("value", sa.Numeric(18, 2), nullable=False, default=0),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index(
        "ix_manual_inputs_period_key",
        "manual_inputs",
        ["period", "metric_key"],
        unique=True,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, default="viewer"),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    """Удаляет все таблицы (откат миграции)."""
    tables = [
        "users", "manual_inputs", "sync_states", "sync_logs", "stock_snapshots",
        "cash_outs", "cash_ins", "payment_outs", "payment_ins",
        "invoice_ins", "invoice_outs",
        "purchase_returns", "sales_returns", "supplies", "demands", "customer_orders",
        "counterparties", "products", "product_folders", "stores",
    ]
    for table in tables:
        op.drop_table(table)
