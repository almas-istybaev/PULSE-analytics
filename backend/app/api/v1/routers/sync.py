"""
Sync router: вебхук от МойСклад и статус синхронизации.
"""
from __future__ import annotations
from typing import Any, Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import require_role
from app.services.sync import SyncService, verify_webhook_signature

router = APIRouter(prefix="/sync", tags=["Синхронизация МойСклад"])


@router.post("/webhook", status_code=200)
async def receive_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_lognex_webhook_signature: str | None = Header(default=None),
) -> dict[str, Any]:
    """Принимает вебхуки от МойСклад и обрабатывает события.

    Верифицирует HMAC-SHA256 подпись и запускает upsert для каждого события.
    Ответ 200 возвращается немедленно; обработка асинхронна.

    Args:
        request: Входящий запрос с телом JSON от МойСклад.
        db: Сессия БД.
        x_lognex_webhook_signature: HMAC подпись из заголовка.

    Returns:
        Количество обработанных событий.

    Raises:
        HTTPException 403: Невалидная подпись вебхука.
    """
    body = await request.body()

    if not verify_webhook_signature(body, x_lognex_webhook_signature or ""):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INVALID_WEBHOOK_SIGNATURE", "message": "Webhook signature is invalid"},
        )

    payload = await request.json()
    events = payload.get("events", [])

    svc = SyncService(db)
    processed = await svc.process_webhook_events(events)

    return {"status": "ok", "events_received": len(events), "events_processed": processed}


@router.get("/status", dependencies=[Depends(require_role("admin", "cfo"))])
async def get_sync_status(db: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, Any]:
    """Возвращает статус последних синхронизаций.

    Args:
        db: Сессия БД.

    Returns:
        Список последних 10 SyncLog записей.
    """
    from sqlalchemy import select, desc
    from app.models.base import SyncLog
    result = await db.execute(
        select(SyncLog).order_by(desc(SyncLog.started_at)).limit(10)
    )
    logs = result.scalars().all()
    return {
        "logs": [
            {
                "id": log.id,
                "entity_type": log.entity_type,
                "sync_type": log.sync_type,
                "status": log.status,
                "records_processed": log.records_processed,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "finished_at": log.finished_at.isoformat() if log.finished_at else None,
                "error": log.error_message,
            }
            for log in logs
        ]
    }
