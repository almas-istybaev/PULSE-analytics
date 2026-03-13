"""
APScheduler: фоновые задачи синхронизации МойСклад.

Запускает:
- Инкрементальную синхронизацию каждые 15 минут
- Ежедневный снимок остатков в 23:59 Asia/Almaty
"""
from __future__ import annotations

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import get_session_factory

logger = structlog.get_logger(__name__)

_scheduler = AsyncIOScheduler(timezone="Asia/Almaty")


async def _run_incremental_sync() -> None:
    """Задача APScheduler: инкрементальная синхронизация."""
    from app.services.sync import SyncService

    logger.info("Starting scheduled incremental sync")
    async with get_session_factory()() as session:
        try:
            svc = SyncService(session)
            result = await svc.incremental_sync()
            total = sum(v for v in result.values() if v > 0)
            logger.info("Incremental sync complete", total_updated=total)
        except Exception as exc:
            logger.error("Incremental sync failed", error=str(exc))


async def _run_stock_snapshot() -> None:
    """Задача APScheduler: ежедневный снимок остатков."""
    from app.services.sync import SyncService

    logger.info("Starting daily stock snapshot")
    async with get_session_factory()() as session:
        try:
            svc = SyncService(session)
            count = await svc.daily_stock_snapshot()
            logger.info("Stock snapshot complete", records=count)
        except Exception as exc:
            logger.error("Stock snapshot failed", error=str(exc))


def start_scheduler() -> None:
    """Запускает APScheduler с фоновыми задачами.

    Вызывается из lifepan FastAPI при старте приложения.
    """
    _scheduler.add_job(
        _run_incremental_sync,
        trigger=IntervalTrigger(minutes=15),
        id="incremental_sync",
        replace_existing=True,
        misfire_grace_time=60,
    )

    _scheduler.add_job(
        _run_stock_snapshot,
        trigger=CronTrigger(hour=23, minute=59, timezone="Asia/Almaty"),
        id="stock_snapshot",
        replace_existing=True,
        misfire_grace_time=300,
    )

    _scheduler.start()
    logger.info("APScheduler started: incremental_sync every 15 min, stock_snapshot at 23:59")


def stop_scheduler() -> None:
    """Останавливает APScheduler. Вызывается при завершении приложения."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
