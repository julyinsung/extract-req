"""AI 상세요구사항 생성 엔드포인트 라우터.

POST /api/v1/generate — AI 백엔드 SSE 스트리밍으로 상세요구사항을 생성한다.
AI_BACKEND 환경변수로 선택된 백엔드를 팩토리를 통해 주입한다 (REQ-007).
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.api import GenerateRequest
from app.services.ai_backend_factory import get_ai_generate_service

router = APIRouter(prefix="/api/v1")


@router.post("/generate")
async def generate_details(req: GenerateRequest):
    """원본 요구사항을 AI로 분해하여 SSE 스트림으로 반환한다.

    Cache-Control과 X-Accel-Buffering 헤더를 설정하여 프록시/nginx 버퍼링을 방지한다.
    SEC-007-01: 팩토리에서 ImportError 발생 시 503 응답으로 변환한다.

    Args:
        req: session_id를 포함한 생성 요청

    Returns:
        StreamingResponse — text/event-stream 형식의 SSE 스트림
    """
    try:
        service = get_ai_generate_service()
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"AI 백엔드를 초기화할 수 없습니다: {e}")
    return StreamingResponse(
        service.generate_stream(req.session_id, req.req_group),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
