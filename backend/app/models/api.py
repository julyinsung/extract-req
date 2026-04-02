from pydantic import BaseModel, Field
from typing import Literal

from app.models.requirement import OriginalRequirement, DetailRequirement


class ParseResponse(BaseModel):
    """HWP 파싱 완료 응답."""

    session_id: str
    requirements: list[OriginalRequirement]


class GenerateRequest(BaseModel):
    """AI 상세요구사항 생성 요청."""

    session_id: str
    # REQ-009: 생성 완료 후 SDK session_id를 저장할 REQ 그룹 ID
    req_group: str = Field(min_length=1)


class GenerateResponse(BaseModel):
    """AI 생성 완료 응답."""

    details: list[DetailRequirement]


class ChatMessage(BaseModel):
    """채팅 히스토리 항목 (요청 페이로드용)."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """채팅 수정 요청.

    history는 이전 대화 컨텍스트를 Claude API에 전달하기 위해 포함한다.
    req_group은 서버가 컨텍스트 필터링에 사용한다 (REQ-004-05).
    """

    session_id: str
    message: str
    history: list[ChatMessage] = []
    # REQ-004-05: 선택된 REQ 그룹 ID — 빈 문자열 차단
    req_group: str = Field(min_length=1)


class InlineEditRequest(BaseModel):
    """인라인 편집 요청 (REQ-003-03).

    field는 수정 가능한 컬럼만 허용하여 임의 필드 덮어쓰기를 방지한다.
    """

    detail_id: str
    field: Literal["name", "content", "category"]
    value: str


class ErrorResponse(BaseModel):
    """일관된 에러 응답 형식.

    스택 트레이스를 노출하지 않고 code/message만 반환한다.
    """

    code: str
    message: str
