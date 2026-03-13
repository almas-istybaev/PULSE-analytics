"""
Export router: экспорт отчётов в PDF и Excel.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from app.core.dependencies import require_role

router = APIRouter(prefix="/export", tags=["Экспорт"])

@router.get("/{report_type}", dependencies=[Depends(require_role("admin","ceo","cfo"))])
async def export_report(report_type: str, format: str = "pdf"):
    """Экспорт отчёта в PDF или Excel.

    В разработке: требует установки weasyprint/openpyxl.
    """
    return {
        "status": "coming_soon",
        "report_type": report_type,
        "format": format,
        "message": "Export module is under development",
    }
