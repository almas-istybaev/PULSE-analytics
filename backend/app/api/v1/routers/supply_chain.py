"""
Supply Chain router: OTIF (On Time In Full).
"""
from __future__ import annotations
from typing import Annotated, Any
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.base import Supply
from app.schemas.common import PeriodParams

router = APIRouter(prefix="/supply-chain", tags=["Цепи поставок"])

@router.get("/otif", dependencies=[Depends(require_role("admin","ceo","cfo","cco","buyer"))])
async def get_otif(params: Annotated[PeriodParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, Any]:
    """OTIF — On Time In Full (своевременность и полнота поставки)."""
    start = datetime.combine(params.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end = datetime.combine(params.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    total_q = await db.execute(select(func.count(Supply.id)).where(and_(Supply.moment >= start, Supply.moment <= end)))
    total = int(total_q.scalar() or 0)

    return {
        "period": {"start": params.start_date, "end": params.end_date},
        "total_deliveries": total,
        "on_time_pct": 0.0,
        "in_full_pct": 0.0,
        "otif_pct": 0.0,
        "note": "Full OTIF calculation requires delivery date fields from MoySklad supply items",
    }
