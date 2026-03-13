"""
Сервисы оборотного капитала: CCC, A/R Aging, A/P Aging.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Demand, InvoiceIn, InvoiceOut, PaymentIn, PaymentOut, StockSnapshot
from app.schemas.common import PeriodParams


class WorkingCapitalService:
    """Расчёт показателей оборотного капитала (CCC, DIO, DSO, DPO).

    Args:
        db: Асинхронная сессия БД.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_ccc(self, params: PeriodParams) -> dict[str, Any]:
        """Cash Conversion Cycle = DIO + DSO - DPO.

        Args:
            params: Период анализа.

        Returns:
            DIO, DSO, DPO, CCC в днях.
        """
        start = datetime.combine(params.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        days = (params.end_date - params.start_date).days or 1

        # DIO = Средние запасы / (COGS / дни)
        inv_q = await self._db.execute(
            select(func.coalesce(func.avg(StockSnapshot.value), 0)).where(
                and_(StockSnapshot.snapshot_date >= start, StockSnapshot.snapshot_date <= end)
            )
        )
        avg_inventory = Decimal(str(inv_q.scalar() or 0))

        cogs_q = await self._db.execute(
            select(func.coalesce(func.sum(Demand.cogs_sum), 0)).where(
                and_(Demand.moment >= start, Demand.moment <= end)
            )
        )
        cogs = Decimal(str(cogs_q.scalar() or 0))
        daily_cogs = cogs / days if days else Decimal("1")
        dio = float(avg_inventory / daily_cogs) if daily_cogs else 0.0

        # DSO = Средняя дебиторка / (Выручка / дни)
        revenue_q = await self._db.execute(
            select(func.coalesce(func.sum(Demand.sum), 0)).where(
                and_(Demand.moment >= start, Demand.moment <= end)
            )
        )
        revenue = Decimal(str(revenue_q.scalar() or 0))
        daily_revenue = revenue / days if days else Decimal("1")

        ar_q = await self._db.execute(
            select(func.coalesce(func.avg(InvoiceOut.sum - func.coalesce(InvoiceOut.paid_sum, 0)), 0)).where(
                and_(InvoiceOut.moment >= start, InvoiceOut.moment <= end, InvoiceOut.is_paid == False)  # noqa: E712
            )
        )
        avg_ar = Decimal(str(ar_q.scalar() or 0))
        dso = float(avg_ar / daily_revenue) if daily_revenue else 0.0

        # DPO = Средняя кредиторка / (Закупки / дни)
        purchases_q = await self._db.execute(
            select(func.coalesce(func.sum(PaymentOut.sum), 0)).where(
                and_(PaymentOut.moment >= start, PaymentOut.moment <= end)
            )
        )
        purchases = Decimal(str(purchases_q.scalar() or 0))
        daily_purchases = purchases / days if days else Decimal("1")

        ap_q = await self._db.execute(
            select(func.coalesce(func.avg(InvoiceIn.sum - func.coalesce(InvoiceIn.paid_sum, 0)), 0)).where(
                and_(InvoiceIn.moment >= start, InvoiceIn.moment <= end, InvoiceIn.is_paid == False)  # noqa: E712
            )
        )
        avg_ap = Decimal(str(ap_q.scalar() or 0))
        dpo = float(avg_ap / daily_purchases) if daily_purchases else 0.0

        ccc = dio + dso - dpo

        return {
            "period": {"start": params.start_date, "end": params.end_date, "days": days},
            "ccc_days": round(ccc, 1),
            "dio_days": round(dio, 1),
            "dso_days": round(dso, 1),
            "dpo_days": round(dpo, 1),
        }

    async def get_ar_aging(self, params: PeriodParams) -> dict[str, Any]:
        """Дебиторская задолженность по срокам (AR Aging).

        Группирует неоплаченные счета покупателей по buckets:
        0-30, 31-60, 61-90, 91-120, >120 дней.

        Args:
            params: Дата отчёта (end_date — дата среза).

        Returns:
            Список buckets с суммой и количеством счетов.
        """
        as_of = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        result = await self._db.execute(
            select(
                InvoiceOut.id,
                InvoiceOut.name,
                InvoiceOut.moment,
                InvoiceOut.sum,
                InvoiceOut.paid_sum,
                InvoiceOut.counterparty_id,
            ).where(
                and_(InvoiceOut.moment <= as_of, InvoiceOut.is_paid == False)  # noqa: E712
            )
        )
        rows = result.all()

        buckets: dict[str, dict[str, Any]] = {
            "0_30": {"label": "0-30 дней", "total": Decimal("0"), "count": 0, "invoices": []},
            "31_60": {"label": "31-60 дней", "total": Decimal("0"), "count": 0, "invoices": []},
            "61_90": {"label": "61-90 дней", "total": Decimal("0"), "count": 0, "invoices": []},
            "91_120": {"label": "91-120 дней", "total": Decimal("0"), "count": 0, "invoices": []},
            "120_plus": {"label": ">120 дней", "total": Decimal("0"), "count": 0, "invoices": []},
        }

        for row in rows:
            if row.moment is None:
                continue
            overdue_days = (params.end_date - row.moment.date()).days
            outstanding = (row.sum or Decimal("0")) - (row.paid_sum or Decimal("0"))

            if overdue_days <= 30:
                key = "0_30"
            elif overdue_days <= 60:
                key = "31_60"
            elif overdue_days <= 90:
                key = "61_90"
            elif overdue_days <= 120:
                key = "91_120"
            else:
                key = "120_plus"

            buckets[key]["total"] += outstanding
            buckets[key]["count"] += 1

        return {
            "as_of_date": params.end_date,
            "currency": params.currency,
            "buckets": [
                {
                    "key": k,
                    "label": v["label"],
                    "total": float(v["total"]),
                    "count": v["count"],
                }
                for k, v in buckets.items()
            ],
            "grand_total": float(sum(v["total"] for v in buckets.values())),
        }

    async def get_ap_aging(self, params: PeriodParams) -> dict[str, Any]:
        """Кредиторская задолженность по срокам (AP Aging).

        Аналогично AR Aging, но по счетам поставщиков.

        Args:
            params: Дата среза.

        Returns:
            Список buckets с суммой и количеством счетов.
        """
        as_of = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        result = await self._db.execute(
            select(
                InvoiceIn.id,
                InvoiceIn.moment,
                InvoiceIn.sum,
                InvoiceIn.paid_sum,
            ).where(
                and_(InvoiceIn.moment <= as_of, InvoiceIn.is_paid == False)  # noqa: E712
            )
        )
        rows = result.all()

        buckets: dict[str, dict[str, Any]] = {
            "0_30": {"label": "0-30 дней", "total": Decimal("0"), "count": 0},
            "31_60": {"label": "31-60 дней", "total": Decimal("0"), "count": 0},
            "61_90": {"label": "61-90 дней", "total": Decimal("0"), "count": 0},
            "91_120": {"label": "91-120 дней", "total": Decimal("0"), "count": 0},
            "120_plus": {"label": ">120 дней", "total": Decimal("0"), "count": 0},
        }

        for row in rows:
            if row.moment is None:
                continue
            overdue_days = (params.end_date - row.moment.date()).days
            outstanding = (row.sum or Decimal("0")) - (row.paid_sum or Decimal("0"))

            if overdue_days <= 30:
                key = "0_30"
            elif overdue_days <= 60:
                key = "31_60"
            elif overdue_days <= 90:
                key = "61_90"
            elif overdue_days <= 120:
                key = "91_120"
            else:
                key = "120_plus"

            buckets[key]["total"] += outstanding
            buckets[key]["count"] += 1

        return {
            "as_of_date": params.end_date,
            "currency": params.currency,
            "buckets": [
                {"key": k, "label": v["label"], "total": float(v["total"]), "count": v["count"]}
                for k, v in buckets.items()
            ],
            "grand_total": float(sum(v["total"] for v in buckets.values())),
        }
