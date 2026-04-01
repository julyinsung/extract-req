"""AI 상세요구사항 생성 엔드포인트 라우터.

POST /api/v1/generate — Claude API SSE 스트리밍으로 상세요구사항을 생성한다.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.api import GenerateRequest
from app.services.ai_generate_service import AiGenerateService

router = APIRouter(prefix="/api/v1")


@router.post("/generate")
async def generate_details(req: GenerateRequest):
    """원본 요구사항을 AI로 분해하여 SSE 스트림으로 반환한다.

    Cache-Control과 X-Accel-Buffering 헤더를 설정하여 프록시/nginx 버퍼링을 방지한다.

    Args:
        req: session_id를 포함한 생성 요청

    Returns:
        StreamingResponse — text/event-stream 형식의 SSE 스트림
    """
    service = AiGenerateService()
    return StreamingResponse(
        service.generate_stream(req.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
