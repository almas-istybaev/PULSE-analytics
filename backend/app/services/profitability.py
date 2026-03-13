"""
Сервисы рентабельности и инвесторских показателей: EBITDA, ROE (DuPont), CAPEX.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Demand, ManualInput, PaymentIn, PaymentOut, SalesReturn
from app.schemas.common import GroupByParams, PeriodParams


class ProfitabilityService:
    """EBITDA, EBITDA Bridge (Waterfall)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_ebitda(self, params: GroupByParams) -> dict[str, Any]:
        """Рассчитывает EBITDA и строит Waterfall (Bridge).

        EBITDA = Выручка - COGS - OPEX + Амортизация (из ManualInput).

        Args:
            params: Период и группировка.

        Returns:
            EBITDA, маржа, Bridge-данные для waterfall-чарта.
        """
        start = datetime.combine(params.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        rev_q = await self._db.execute(
            select(func.coalesce(func.sum(Demand.sum), 0)).where(
                and_(Demand.moment >= start, Demand.moment <= end)
            )
        )
        revenue = Decimal(str(rev_q.scalar() or 0))

        ret_q = await self._db.execute(
            select(func.coalesce(func.sum(SalesReturn.sum), 0)).where(
                and_(SalesReturn.moment >= start, SalesReturn.moment <= end)
            )
        )
        returns = Decimal(str(ret_q.scalar() or 0))
        net_revenue = revenue - returns

        cogs_q = await self._db.execute(
            select(func.coalesce(func.sum(Demand.cogs_sum), 0)).where(
                and_(Demand.moment >= start, Demand.moment <= end)
            )
        )
        cogs = Decimal(str(cogs_q.scalar() or 0))

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

        # Амортизация из ManualInput
        amort_q = await self._db.execute(
            select(func.coalesce(func.sum(ManualInput.amount), 0)).where(
                ManualInput.input_type == "DEPRECIATION"
            )
        )
        depreciation = Decimal(str(amort_q.scalar() or 0))

        ebitda = net_revenue - cogs - opex + depreciation
        margin = float(ebitda / net_revenue * 100) if net_revenue else 0.0

        return {
            "period": {"start": params.start_date, "end": params.end_date},
            "currency": params.currency,
            "revenue": float(net_revenue),
            "cogs": float(cogs),
            "opex": float(opex),
            "depreciation": float(depreciation),
            "ebitda": float(ebitda),
            "ebitda_margin_pct": round(margin, 2),
            "bridge": [
                {"label": "Выручка", "value": float(net_revenue), "type": "total"},
                {"label": "Себестоимость", "value": float(-cogs), "type": "decrease"},
                {"label": "Операционные расходы", "value": float(-opex), "type": "decrease"},
                {"label": "Амортизация (add-back)", "value": float(depreciation), "type": "increase"},
                {"label": "EBITDA", "value": float(ebitda), "type": "total"},
            ],
        }


class InvestorService:
    """CAPEX, ROE (DuPont), Дивиденды."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_capex(self, params: PeriodParams) -> dict[str, Any]:
        """CAPEX — капитальные расходы за период.

        Args:
            params: Период анализа.

        Returns:
            Общий CAPEX, по категориям, с планом из ManualInput.
        """
        start = datetime.combine(params.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        # CAPEX из исходящих платежей
        capex_q = await self._db.execute(
            select(func.coalesce(func.sum(PaymentOut.sum), 0)).where(
                and_(
                    PaymentOut.moment >= start,
                    PaymentOut.moment <= end,
                    PaymentOut.expense_type == "CAPEX",
                )
            )
        )
        capex_actual = Decimal(str(capex_q.scalar() or 0))

        # CAPEX план из ManualInput
        period_str = params.start_date.strftime("%Y-%m")
        plan_q = await self._db.execute(
            select(func.coalesce(func.sum(ManualInput.amount), 0)).where(
                and_(ManualInput.input_type == "CAPEX", ManualInput.period >= period_str)
            )
        )
        capex_plan = Decimal(str(plan_q.scalar() or 0))

        return {
            "period": {"start": params.start_date, "end": params.end_date},
            "currency": params.currency,
            "actual": float(capex_actual),
            "plan": float(capex_plan),
            "variance": float(capex_actual - capex_plan),
            "variance_pct": round(float((capex_actual - capex_plan) / capex_plan * 100), 2) if capex_plan else 0.0,
        }

    async def get_dividends(self, params: PeriodParams) -> dict[str, Any]:
        """Дивиденды за период.

        Args:
            params: Период.

        Returns:
            Выплаченные дивиденды по платежам и ручному вводу.
        """
        start = datetime.combine(params.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        div_q = await self._db.execute(
            select(func.coalesce(func.sum(PaymentOut.sum), 0)).where(
                and_(
                    PaymentOut.moment >= start,
                    PaymentOut.moment <= end,
                    PaymentOut.expense_type == "DIVIDENDS",
                )
            )
        )
        dividends = Decimal(str(div_q.scalar() or 0))

        return {
            "period": {"start": params.start_date, "end": params.end_date},
            "currency": params.currency,
            "total_paid": float(dividends),
        }
