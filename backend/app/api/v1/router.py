"""
Главный роутер v1 — объединяет все подроутеры API Pulse.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.financial import router as financial_router
from app.api.v1.routers.business import (
    wc_router,
    inv_router,
    analytics_router,
    prof_router,
    investor_router,
)
from app.api.v1.routers.sync import router as sync_router
from app.api.v1.routers.export import router as export_router
from app.api.v1.routers.dashboards import router as dashboards_router
from app.api.v1.routers.supply_chain import router as supply_chain_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(financial_router)
api_router.include_router(wc_router)
api_router.include_router(inv_router)
api_router.include_router(analytics_router)
api_router.include_router(prof_router)
api_router.include_router(investor_router)
api_router.include_router(sync_router)
api_router.include_router(export_router)
api_router.include_router(dashboards_router)
api_router.include_router(supply_chain_router)
