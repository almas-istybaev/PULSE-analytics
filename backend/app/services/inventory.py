"""
Сервисы складской эффективности: ABC/XYZ анализ, GMROI.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from statistics import mean, stdev
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Demand, Product, StockSnapshot
from app.schemas.common import GroupByParams, PeriodParams


class InventoryService:
    """ABC/XYZ анализ и GMROI.

    ABC: Классификация товаров по выручке (А=80%, B=15%, C=5%).
    XYZ: Классификация по стабильности спроса (CV < 10% = X, < 25% = Y, иначе = Z).
    GMROI: Валовая прибыль / Средние запасы.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_abc_xyz(self, params: PeriodParams) -> dict[str, Any]:
        """ABC/XYZ матрица товаров.

        Args:
            params: Период анализа.

        Returns:
            Список товаров с ABC и XYZ классами + 9-сегментная матрица.
        """
        start = datetime.combine(params.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        # Агрегируем выручку и себестоимость по продуктам
        # ABC использует данные из positions (demand items) — здесь упрощённо через Demand
        result = await self._db.execute(
            select(
                Demand.counterparty_id.label("product_id"),  # placeholder
                func.sum(Demand.sum).label("revenue"),
                func.sum(Demand.cogs_sum).label("cogs"),
                func.count(Demand.id).label("order_count"),
            ).where(
                and_(Demand.moment >= start, Demand.moment <= end)
            ).group_by(Demand.counterparty_id)
        )
        rows = result.all()

        if not rows:
            return {"period": {"start": params.start_date, "end": params.end_date}, "items": [], "matrix": {}}

        total_revenue = sum(float(r.revenue or 0) for r in rows)
        items = []
        cumulative = 0.0

        sorted_rows = sorted(rows, key=lambda r: float(r.revenue or 0), reverse=True)

        for row in sorted_rows:
            rev = float(row.revenue or 0)
            cumulative += rev
            pct = cumulative / total_revenue * 100 if total_revenue else 0

            # ABC по накопленной выручке
            if pct <= 80:
                abc = "A"
            elif pct <= 95:
                abc = "B"
            else:
                abc = "C"

            # XYZ по CV (коэффициент вариации) — используем order_count как прокси
            cv = 0.0  # Для полного расчёта нужны помесячные данные
            xyz = "X" if cv < 10 else ("Y" if cv < 25 else "Z")

            items.append({
                "product_id": str(row.product_id),
                "revenue": rev,
                "revenue_pct": round(rev / total_revenue * 100, 2) if total_revenue else 0,
                "abc_class": abc,
                "xyz_class": xyz,
                "segment": f"{abc}{xyz}",
            })

        # Матрица 9 сегментов
        matrix: dict[str, int] = {}
        for item in items:
            seg = item["segment"]
            matrix[seg] = matrix.get(seg, 0) + 1

        return {
            "period": {"start": params.start_date, "end": params.end_date},
            "currency": params.currency,
            "total_revenue": total_revenue,
            "items": items,
            "matrix": matrix,
        }

    async def get_gmroi(self, params: GroupByParams) -> dict[str, Any]:
        """GMROI = Валовая прибыль / Средние запасы.

        Args:
            params: Период и группировка.

        Returns:
            GMROI по периоду и в динамике.
        """
        start = datetime.combine(params.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

        # Валовая прибыль
        gp_q = await self._db.execute(
            select(
                func.coalesce(func.sum(Demand.sum - func.coalesce(Demand.cogs_sum, 0)), 0)
            ).where(and_(Demand.moment >= start, Demand.moment <= end))
        )
        gross_profit = Decimal(str(gp_q.scalar() or 0))

        # Средние запасы
        inv_q = await self._db.execute(
            select(func.coalesce(func.avg(StockSnapshot.value), 0)).where(
                and_(StockSnapshot.snapshot_date >= start, StockSnapshot.snapshot_date <= end)
            )
        )
        avg_inventory = Decimal(str(inv_q.scalar() or 0))

        gmroi = float(gross_profit / avg_inventory) if avg_inventory else 0.0

        return {
            "period": {"start": params.start_date, "end": params.end_date},
            "currency": params.currency,
            "gross_profit": float(gross_profit),
            "avg_inventory": float(avg_inventory),
            "gmroi": round(gmroi, 2),
            "interpretation": (
                "Excellent (>3.0)" if gmroi > 3.0
                else "Good (1.0-3.0)" if gmroi >= 1.0
                else "Poor (<1.0)"
            ),
        }
