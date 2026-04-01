"""채팅 기반 AI 수정 라우터 (REQ-004).

POST /api/v1/chat — SSE 스트리밍으로 채팅 응답과 PATCH 이벤트를 반환한다.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.api import ChatRequest
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1")


@router.post("/chat")
async def chat(req: ChatRequest):
    """채팅 메시지를 받아 Claude API 스트리밍 응답을 SSE로 반환한다.

    Args:
        req: session_id, message, history를 포함한 채팅 요청

    Returns:
        SSE 스트리밍 응답 (text | patch | done | error 이벤트)
    """
    service = ChatService()
    return StreamingResponse(
        service.chat_stream(req.session_id, req.message, req.history),
        media_type="text/event-stream",
        # 프록시/nginx가 응답을 버퍼링하지 않도록 캐시 비활성화
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
