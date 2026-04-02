"""채팅 기반 AI 수정 라우터 (REQ-004, REQ-007).

POST /api/v1/chat — SSE 스트리밍으로 채팅 응답과 PATCH 이벤트를 반환한다.
AI_BACKEND 환경변수로 선택된 백엔드를 팩토리를 통해 주입한다 (REQ-007).
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.api import ChatRequest
from app.services.ai_backend_factory import get_chat_service

router = APIRouter(prefix="/api/v1")


@router.post("/chat")
async def chat(req: ChatRequest):
    """채팅 메시지를 받아 AI 스트리밍 응답을 SSE로 반환한다.

    SEC-007-01: 팩토리에서 ImportError 발생 시 503 응답으로 변환한다.

    Args:
        req: session_id, message, history를 포함한 채팅 요청

    Returns:
        SSE 스트리밍 응답 (text | patch | done | error 이벤트)
    """
    try:
        service = get_chat_service()
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"AI 백엔드를 초기화할 수 없습니다: {e}")
    return StreamingResponse(
        service.chat_stream(req.session_id, req.message, req.history, req.req_group),
        media_type="text/event-stream",
        # 프록시/nginx가 응답을 버퍼링하지 않도록 캐시 비활성화
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
