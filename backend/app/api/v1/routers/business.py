"""
Роутеры оборотного капитала, инвентаря, аналитики, рентабельности, инвестиций.
"""
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import require_role
from app.schemas.common import GroupByParams, PeriodParams
from app.services.working_capital import WorkingCapitalService
from app.services.inventory import InventoryService
from app.services.analytics import AnalyticsService
from app.services.profitability import ProfitabilityService, InvestorService

# ── Working Capital ──
wc_router = APIRouter(prefix="/working-capital", tags=["Оборотный капитал"])

@wc_router.get("/ccc", dependencies=[Depends(require_role("admin","ceo","cfo"))])
async def get_ccc(params: Annotated[PeriodParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """CCC — Cash Conversion Cycle."""
    return await WorkingCapitalService(db).get_ccc(params)

@wc_router.get("/ar-aging", dependencies=[Depends(require_role("admin","ceo","cfo","cco"))])
async def get_ar_aging(params: Annotated[PeriodParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """Дебиторская задолженность по срокам."""
    return await WorkingCapitalService(db).get_ar_aging(params)

@wc_router.get("/ap-aging", dependencies=[Depends(require_role("admin","ceo","cfo"))])
async def get_ap_aging(params: Annotated[PeriodParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """Кредиторская задолженность по срокам."""
    return await WorkingCapitalService(db).get_ap_aging(params)


# ── Inventory ──
inv_router = APIRouter(prefix="/inventory", tags=["Запасы"])

@inv_router.get("/abc-xyz", dependencies=[Depends(require_role("admin","ceo","cfo","cco","buyer"))])
async def get_abc_xyz(params: Annotated[PeriodParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """ABC/XYZ анализ товаров."""
    return await InventoryService(db).get_abc_xyz(params)

@inv_router.get("/gmroi", dependencies=[Depends(require_role("admin","ceo","cfo","buyer"))])
async def get_gmroi(params: Annotated[GroupByParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """GMROI — отдача на инвестиции в запасы."""
    return await InventoryService(db).get_gmroi(params)


# ── Analytics ──
analytics_router = APIRouter(prefix="/analytics", tags=["Аналитика"])

class CACInputRequest(BaseModel):
    period: str
    channel: str
    spend: float
    new_customers: int

@analytics_router.get("/ltv-cac", dependencies=[Depends(require_role("admin","ceo","cfo","cco"))])
async def get_ltv_cac(params: Annotated[PeriodParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """LTV/CAC анализ."""
    return await AnalyticsService(db).get_ltv_cac(params)

@analytics_router.post("/cac-input", dependencies=[Depends(require_role("admin","cfo","cco"))])
async def create_cac_input(body: CACInputRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """Ввод маркетинговых расходов для расчёта CAC."""
    return await AnalyticsService(db).create_cac_input(
        period=body.period,
        channel=body.channel,
        spend=body.spend,
        new_customers=body.new_customers,
    )


# ── Profitability ──
prof_router = APIRouter(prefix="/profitability", tags=["Рентабельность"])

@prof_router.get("/ebitda", dependencies=[Depends(require_role("admin","ceo","cfo"))])
async def get_ebitda(params: Annotated[GroupByParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """EBITDA и Waterfall Bridge."""
    return await ProfitabilityService(db).get_ebitda(params)


# ── Investor ──
investor_router = APIRouter(prefix="/investor", tags=["Инвесторские показатели"])

@investor_router.get("/capex", dependencies=[Depends(require_role("admin","ceo","cfo","investor"))])
async def get_capex(params: Annotated[PeriodParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """CAPEX — капитальные расходы."""
    return await InvestorService(db).get_capex(params)

@investor_router.get("/dividends", dependencies=[Depends(require_role("admin","ceo","cfo","investor"))])
async def get_dividends(params: Annotated[PeriodParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """Дивиденды за период."""
    return await InvestorService(db).get_dividends(params)
