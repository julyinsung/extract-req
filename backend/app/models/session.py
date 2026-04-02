from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime
import uuid

from app.models.requirement import OriginalRequirement, DetailRequirement


class ChatMessage(BaseModel):
    """사용자-AI 채팅 메시지 1건."""

    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionState(BaseModel):
    """서버 프로세스 수명 동안 유지되는 단일 세션 상태.

    상태 전이: idle → parsed → generated → done
    새 HWP 업로드 시 reset_session()으로 전체 초기화된다.
    """

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["idle", "parsed", "generated", "done"] = "idle"
    original_requirements: list[OriginalRequirement] = []
    detail_requirements: list[DetailRequirement] = []
    chat_messages: list[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # REQ-009: claude-agent-sdk 세션 연속 실행을 위한 session_id.
    # reset_session()이 새 SessionState()를 생성할 때 자동으로 None으로 초기화된다.
    sdk_session_id: str | None = None
