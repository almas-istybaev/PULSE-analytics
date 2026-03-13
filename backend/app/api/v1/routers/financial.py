"""
Финансовые отчёты: ОДДС, ОПиУ, Баланс.
"""
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_role
from app.schemas.common import GroupByParams, PeriodParams
from app.services.financial import CashFlowService, IncomeStatementService, BalanceSheetService

router = APIRouter(prefix="/financial", tags=["Финансовые отчёты"])

@router.get("/cash-flow", dependencies=[Depends(require_role("admin","ceo","cfo","cco"))])
async def get_cash_flow(params: Annotated[GroupByParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """ОДДС — Отчёт о движении денежных средств."""
    return await CashFlowService(db).get_report(params)

@router.get("/income-statement", dependencies=[Depends(require_role("admin","ceo","cfo","cco"))])
async def get_income_statement(params: Annotated[GroupByParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """ОПиУ — Отчёт о прибылях и убытках."""
    return await IncomeStatementService(db).get_report(params)

@router.get("/balance-sheet", dependencies=[Depends(require_role("admin","ceo","cfo"))])
async def get_balance_sheet(params: Annotated[PeriodParams, Depends()], db: Annotated[AsyncSession, Depends(get_db)]):
    """Баланс — Балансовый отчёт."""
    return await BalanceSheetService(db).get_report(params)
