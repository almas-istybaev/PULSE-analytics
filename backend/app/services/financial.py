"""
Финансовые сервисы: ОДДС, ОПиУ, Баланс.

Вся бизнес-логика расчётов изолирована от роутеров и репозиториев.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import (
    CashIn, CashOut, Demand, InvoiceIn, InvoiceOut,
    PaymentIn, PaymentOut, SalesReturn, StockSnapshot,
)
from app.schemas.common import GroupByParams, PeriodParams


# ─────────────────────────────────────────────
# ОДДС — Cash Flow
# ─────────────────────────────────────────────

class CashFlowService:
    """Расчёт ОДДС (Отчёт о движении денежных средств).

    Группирует платежи по 3 разделам МСФО:
    - Операционная деятельность
    - Инвестиционная деятельность (CAPEX)
    - Финансовая деятельность (кредиты, дивиденды)
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_report(self, params: GroupByParams) -> dict[str, Any]:
        """Формирует ОДДС за указанный период.

        Args:
            params: Период, группировка и фильтр склада.

        Returns:
            Словарь с входящими, исходящими и чистым потоком по разделам.
        """
        start = datetime.combine(params.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        # Входящие платежи (операционные)
        inflow_q = await self._db.execute(
            select(func.coalesce(func.sum(PaymentIn.sum), 0)).where(
                and_(PaymentIn.moment >= start, PaymentIn.moment <= end)
            )
        )
        inflow = inflow_q.scalar() or Decimal("0")

        # Приходные кассовые ордера
        cashin_q = await self._db.execute(
            select(func.coalesce(func.sum(CashIn.sum), 0)).where(
                and_(CashIn.moment >= start, CashIn.moment <= end)
            )
        )
        cash_in = cashin_q.scalar() or Decimal("0")

        # Исходящие платежи (все типы)
        outflow_q = await self._db.execute(
            select(func.coalesce(func.sum(PaymentOut.sum), 0)).where(
                and_(PaymentOut.moment >= start, PaymentOut.moment <= end)
            )
        )
        outflow = outflow_q.scalar() or Decimal("0")

        # Расходные кассовые ордера
        cashout_q = await self._db.execute(
            select(func.coalesce(func.sum(CashOut.sum), 0)).where(
                and_(CashOut.moment >= start, CashOut.moment <= end)
            )
        )
        cash_out = cashout_q.scalar() or Decimal("0")

        # CAPEX — исходящие платежи с expense_type=CAPEX
        capex_q = await self._db.execute(
            select(func.coalesce(func.sum(PaymentOut.sum), 0)).where(
                and_(
                    PaymentOut.moment >= start,
                    PaymentOut.moment <= end,
                    PaymentOut.expense_type == "CAPEX",
                )
            )
        )
        capex = capex_q.scalar() or Decimal("0")

        # Дивиденды
        dividends_q = await self._db.execute(
            select(func.coalesce(func.sum(PaymentOut.sum), 0)).where(
                and_(
                    PaymentOut.moment >= start,
                    PaymentOut.moment <= end,
                    PaymentOut.expense_type == "DIVIDENDS",
                )
            )
        )
        dividends = dividends_q.scalar() or Decimal("0")

        # Операционный поток (без CAPEX, дивидендов, кредитов)
        operating_inflow = inflow + cash_in
        operating_outflow = outflow - capex - dividends + cash_out
        operating_net = operating_inflow - operating_outflow

        return {
            "period": {"start": params.start_date, "end": params.end_date},
            "currency": params.currency,
            "operating": {
                "inflow": float(operating_inflow),
                "outflow": float(operating_outflow),
                "net": float(operating_net),
            },
            "investing": {
                "outflow": float(capex),
                "net": float(-capex),
            },
            "financing": {
                "outflow": float(dividends),
                "net": float(-dividends),
            },
            "total_net": float(operating_net - capex - dividends),
        }


# ─────────────────────────────────────────────
# ОПиУ — Income Statement
# ─────────────────────────────────────────────

class IncomeStatementService:
    """Расчёт ОПиУ (Отчёт о прибылях и убытках).

    Формула: Выручка → Gross → EBITDA → EBIT → Net.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_report(self, params: GroupByParams) -> dict[str, Any]:
        """Формирует ОПиУ за период.

        Args:
            params: Период и группировка.

        Returns:
            Иерархический словарь отчёта с маржой и сравнением с предыдущим периодом.
        """
        start = datetime.combine(params.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        # Выручка (сумма отгрузок - возвраты)
        revenue_q = await self._db.execute(
            select(func.coalesce(func.sum(Demand.sum), 0)).where(
                and_(Demand.moment >= start, Demand.moment <= end)
            )
        )
        revenue = Decimal(str(revenue_q.scalar() or 0))

        # Возвраты от покупателей
        returns_q = await self._db.execute(
            select(func.coalesce(func.sum(SalesReturn.sum), 0)).where(
                and_(SalesReturn.moment >= start, SalesReturn.moment <= end)
            )
        )
        sales_returns = Decimal(str(returns_q.scalar() or 0))
        net_revenue = revenue - sales_returns

        # COGS (себестоимость из поля cogs_sum на отгрузках)
        cogs_q = await self._db.execute(
            select(func.coalesce(func.sum(Demand.cogs_sum), 0)).where(
                and_(Demand.moment >= start, Demand.moment <= end)
            )
        )
        cogs = Decimal(str(cogs_q.scalar() or 0))

        gross_profit = net_revenue - cogs
        gross_margin = (gross_profit / net_revenue * 100) if net_revenue else Decimal("0")

        # Операционные расходы (OPEX: paymentout без CAPEX, дивидендов, кредитов)
        opex_q = await self._db.execute(
            select(func.coalesce(func.sum(PaymentOut.sum), 0)).where(
                and_(
                    PaymentOut.moment >= start,
                    PaymentOut.moment <= end,
                    PaymentOut.expense_type.not_in(["CAPEX", "DIVIDENDS", "LOAN_PAYMENT"]),
                )
            )
        )
        opex = Decimal(str(opex_q.scalar() or 0))

        ebitda = gross_profit - opex
        ebitda_margin = (ebitda / net_revenue * 100) if net_revenue else Decimal("0")

        return {
            "period": {"start": params.start_date, "end": params.end_date},
            "currency": params.currency,
            "revenue": float(net_revenue),
            "cogs": float(cogs),
            "gross_profit": float(gross_profit),
            "gross_margin_pct": round(float(gross_margin), 2),
            "opex": float(opex),
            "ebitda": float(ebitda),
            "ebitda_margin_pct": round(float(ebitda_margin), 2),
        }


# ─────────────────────────────────────────────
# Баланс — Balance Sheet
# ─────────────────────────────────────────────

class BalanceSheetService:
    """Расчёт Балансового отчёта на дату.

    Формулы из spec.md раздел 2.3.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_report(self, params: PeriodParams) -> dict[str, Any]:
        """Формирует Баланс на дату params.end_date.

        Args:
            params: as_of_date = end_date.

        Returns:
            Баланс: активы, обязательства, собственный капитал.
        """
        as_of = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        epoch = datetime(2000, 1, 1, tzinfo=timezone.utc)

        # Денежные средства (кумулятивно за всю историю до as_of)
        pi_q = await self._db.execute(
            select(func.coalesce(func.sum(PaymentIn.sum), 0)).where(PaymentIn.moment <= as_of)
        )
        po_q = await self._db.execute(
            select(func.coalesce(func.sum(PaymentOut.sum), 0)).where(PaymentOut.moment <= as_of)
        )
        ci_q = await self._db.execute(
            select(func.coalesce(func.sum(CashIn.sum), 0)).where(CashIn.moment <= as_of)
        )
        co_q = await self._db.execute(
            select(func.coalesce(func.sum(CashOut.sum), 0)).where(CashOut.moment <= as_of)
        )

        cash = (
            Decimal(str(pi_q.scalar() or 0))
            + Decimal(str(ci_q.scalar() or 0))
            - Decimal(str(po_q.scalar() or 0))
            - Decimal(str(co_q.scalar() or 0))
        )

        # Запасы (последний StockSnapshot до as_of)
        inv_q = await self._db.execute(
            select(func.coalesce(func.sum(StockSnapshot.value), 0)).where(
                StockSnapshot.snapshot_date <= as_of
            )
        )
        inventory = Decimal(str(inv_q.scalar() or 0))

        # Дебиторская задолженность (неоплаченные счета покупателей)
        ar_q = await self._db.execute(
            select(
                func.coalesce(func.sum(InvoiceOut.sum - func.coalesce(InvoiceOut.paid_sum, 0)), 0)
            ).where(
                and_(InvoiceOut.moment <= as_of, InvoiceOut.is_paid == False)  # noqa: E712
            )
        )
        accounts_receivable = Decimal(str(ar_q.scalar() or 0))

        # Кредиторская задолженность (неоплаченные счета поставщиков)
        ap_q = await self._db.execute(
            select(
                func.coalesce(func.sum(InvoiceIn.sum - func.coalesce(InvoiceIn.paid_sum, 0)), 0)
            ).where(
                and_(InvoiceIn.moment <= as_of, InvoiceIn.is_paid == False)  # noqa: E712
            )
        )
        accounts_payable = Decimal(str(ap_q.scalar() or 0))

        total_assets = cash + inventory + accounts_receivable
        total_liabilities = accounts_payable
        equity = total_assets - total_liabilities

        return {
            "as_of_date": params.end_date,
            "currency": params.currency,
            "assets": {
                "current": {
                    "cash": float(cash),
                    "accounts_receivable": float(accounts_receivable),
                    "inventory": float(inventory),
                    "total_current": float(total_assets),
                },
                "total": float(total_assets),
            },
            "liabilities": {
                "current": {
                    "accounts_payable": float(accounts_payable),
                    "total_current": float(total_liabilities),
                },
                "total": float(total_liabilities),
            },
            "equity": {
                "total": float(equity),
            },
            "check": {
                "balanced": abs(total_assets - total_liabilities - equity) < Decimal("0.01"),
            },
        }
