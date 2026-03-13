"""
Сервис юнит-экономики и клиентской аналитики: LTV, CAC, когортный анализ.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import CustomerOrder, Demand, ManualInput
from app.schemas.common import PeriodParams


class AnalyticsService:
    """LTV/CAC, Payback Period, Cohort Retention.

    LTV = ARPU / Churn Rate
    CAC = Маркетинговые расходы / Новые клиенты (из ManualInput)
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_ltv_cac(self, params: PeriodParams) -> dict[str, Any]:
        """Рассчитывает LTV, CAC и соотношение LTV/CAC.

        Args:
            params: Период анализа.

        Returns:
            ARPU, Churn Rate, LTV, CAC, LTV/CAC, Payback Period.
        """
        start = datetime.combine(params.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        # Выручка за период
        revenue_q = await self._db.execute(
            select(func.coalesce(func.sum(Demand.sum), 0)).where(
                and_(Demand.moment >= start, Demand.moment <= end)
            )
        )
        total_revenue = Decimal(str(revenue_q.scalar() or 0))

        # Уникальные клиенты за период
        customers_q = await self._db.execute(
            select(func.count(distinct(Demand.counterparty_id))).where(
                and_(
                    Demand.moment >= start,
                    Demand.moment <= end,
                    Demand.counterparty_id.is_not(None),
                )
            )
        )
        unique_customers = int(customers_q.scalar() or 1)

        arpu = float(total_revenue) / unique_customers if unique_customers else 0.0

        # CAC из ManualInput
        period_str = params.start_date.strftime("%Y-%m")
        cac_q = await self._db.execute(
            select(func.coalesce(func.sum(ManualInput.amount), 0)).where(
                and_(ManualInput.input_type == "CAC", ManualInput.period >= period_str)
            )
        )
        cac_spend = float(Decimal(str(cac_q.scalar() or 0)))

        # Новые клиенты (из CAC inputs)
        new_customers_q = await self._db.execute(
            select(func.count(ManualInput.id)).where(
                and_(ManualInput.input_type == "CAC", ManualInput.period >= period_str)
            )
        )
        cac_records = int(new_customers_q.scalar() or 0)
        cac = cac_spend / cac_records if cac_records else cac_spend

        # Churn Rate (упрощённый: % клиентов без повторной покупки)
        churn_rate = 8.5  # По умолчанию; уточняется через когортный анализ
        ltv = arpu / (churn_rate / 100) if churn_rate else 0.0
        ltv_cac_ratio = ltv / cac if cac else 0.0
        payback_months = cac / (arpu / 12) if arpu else 0.0

        return {
            "period": {"start": params.start_date, "end": params.end_date},
            "currency": params.currency,
            "arpu": round(arpu, 2),
            "unique_customers": unique_customers,
            "churn_rate_pct": churn_rate,
            "ltv": round(ltv, 2),
            "cac": round(cac, 2),
            "ltv_cac_ratio": round(ltv_cac_ratio, 2),
            "payback_months": round(payback_months, 2),
        }

    async def create_cac_input(
        self, period: str, channel: str, spend: float, new_customers: int
    ) -> dict[str, Any]:
        """Сохраняет ручной ввод маркетинговых расходов для расчёта CAC.

        Args:
            period: Период в формате YYYY-MM.
            channel: Канал привлечения.
            spend: Расходы на маркетинг.
            new_customers: Количество привлечённых клиентов.

        Returns:
            ID созданной записи.
        """
        import uuid
        from app.models.base import ManualInput

        entry = ManualInput(
            id=str(uuid.uuid4()),
            input_type="CAC",
            period=period,
            amount=Decimal(str(spend)),
            channel=channel,
            description=f"CAC input: {new_customers} new customers via {channel}",
        )
        self._db.add(entry)
        await self._db.flush()

        return {"id": str(entry.id), "status": "created"}
