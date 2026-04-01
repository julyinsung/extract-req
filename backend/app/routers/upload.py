"""HWP 업로드 엔드포인트 라우터.

POST /api/v1/upload — HWP 파일을 수신하여 파싱 결과를 반환한다.
"""

from fastapi import APIRouter, File, UploadFile

from app.models.api import ParseResponse
from app.services.hwp_parse_service import HwpParseService

router = APIRouter(prefix="/api/v1")


@router.post("/upload", response_model=ParseResponse)
async def upload_hwp(file: UploadFile = File(...)):
    """HWP 파일을 업로드하고 파싱된 요구사항 목록을 반환한다.

    Args:
        file: multipart/form-data로 전송된 HWP 파일

    Returns:
        ParseResponse — session_id와 requirements 목록
    """
    service = HwpParseService()
    return await service.parse(file)
