"""
Admin router: служебные операции (только admin).

Эндпоинты для запуска синхронизации МойСклад вручную и управления системой.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.services.sync import SyncService

router = APIRouter(prefix="/admin", tags=["Администрирование"])


@router.post("/sync/full", dependencies=[Depends(require_role("admin"))])
async def trigger_full_sync(
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Запускает полную синхронизацию всех 15 сущностей МойСклад.

    Синхронизация выполняется в фоне (BackgroundTasks).
    Сразу возвращает подтверждение запуска.

    Args:
        background_tasks: FastAPI background task runner.
        db: Сессия БД.

    Returns:
        Статус запуска задачи.
    """
    async def _do_sync() -> None:
        svc = SyncService(db)
        await svc.full_sync()

    background_tasks.add_task(_do_sync)
    return {
        "status": "started",
        "message": "Full sync launched in background. Check GET /api/v1/sync/status for progress.",
    }


@router.post("/sync/incremental", dependencies=[Depends(require_role("admin"))])
async def trigger_incremental_sync(
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Запускает инкрементальную синхронизацию (только изменения с последнего запуска).

    Args:
        background_tasks: FastAPI background task runner.
        db: Сессия БД.

    Returns:
        Статус запуска задачи.
    """
    async def _do_sync() -> None:
        svc = SyncService(db)
        await svc.incremental_sync()

    background_tasks.add_task(_do_sync)
    return {
        "status": "started",
        "message": "Incremental sync launched in background.",
    }


@router.post("/sync/snapshot", dependencies=[Depends(require_role("admin"))])
async def trigger_stock_snapshot(
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Принудительно создаёт снимок остатков по складам.

    Args:
        background_tasks: FastAPI background task runner.
        db: Сессия БД.

    Returns:
        Статус запуска задачи.
    """
    async def _do_snapshot() -> None:
        svc = SyncService(db)
        await svc.daily_stock_snapshot()

    background_tasks.add_task(_do_snapshot)
    return {"status": "started", "message": "Stock snapshot launched in background."}
