"""엑셀 다운로드 라우터 (REQ-005).

GET /api/v1/download — stage=1|2에 따라 원본 또는 통합 엑셀 파일을 반환한다.
"""

import io
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.services.excel_export_service import ExcelExportService

router = APIRouter(prefix="/api/v1")


@router.get("/download")
def download_excel(
    session_id: str = Query(..., description="현재 세션 ID"),
    stage: int = Query(..., description="다운로드 단계 (1: 원본, 2: 원본+상세)"),
):
    """엑셀 파일을 생성하여 다운로드 응답으로 반환한다.

    Args:
        session_id: 현재 세션 ID
        stage: 1 = 원본 요구사항만, 2 = 원본 + 상세 통합

    Returns:
        xlsx 파일 StreamingResponse

    Raises:
        HTTPException 422: stage가 1 또는 2가 아닌 경우, 또는 stage=2인데 상세 미생성
    """
    if stage not in (1, 2):
        raise HTTPException(
            422,
            detail={"code": "INVALID_STAGE", "message": "stage는 1 또는 2여야 합니다."},
        )

    service = ExcelExportService()
    data = service.export(stage)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = "original" if stage == 1 else "full"
    filename = f"requirements_{label}_{timestamp}.xlsx"

    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
