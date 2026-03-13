"""
Dashboard routers: агрегированные данные для управленческих дашбордов.
"""
from __future__ import annotations
from typing import Annotated, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_role
from app.schemas.common import PeriodParams
from app.services.financial import CashFlowService, IncomeStatementService
from app.schemas.common import GroupByParams

router = APIRouter(prefix="/dashboards", tags=["Дашборды"])

@router.get("/cfo", dependencies=[Depends(require_role("admin","ceo","cfo"))])
async def cfo_dashboard(
    params: Annotated[GroupByParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """CFO Dashboard — агрегированные финансовые KPI.

    Объединяет ОПиУ, ОДДС и баланс в один ответ.
    """
    cash_flow = await CashFlowService(db).get_report(params)
    income = await IncomeStatementService(db).get_report(params)

    return {
        "period": {"start": params.start_date, "end": params.end_date},
        "kpis": {
            "revenue": income.get("revenue", 0),
            "ebitda": income.get("ebitda", 0),
            "ebitda_margin_pct": income.get("ebitda_margin_pct", 0),
            "gross_margin_pct": income.get("gross_margin_pct", 0),
            "operating_cash_flow": cash_flow.get("operating", {}).get("net", 0),
        },
        "cash_flow": cash_flow,
        "income_statement": income,
    }


@router.get("/commercial", dependencies=[Depends(require_role("admin","ceo","cfo","cco"))])
async def commercial_dashboard(
    params: Annotated[GroupByParams, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """CCO Dashboard — коммерческие KPI."""
    income = await IncomeStatementService(db).get_report(params)
    return {
        "period": {"start": params.start_date, "end": params.end_date},
        "kpis": {
            "revenue": income.get("revenue", 0),
            "gross_profit": income.get("gross_profit", 0),
            "gross_margin_pct": income.get("gross_margin_pct", 0),
        },
    }
