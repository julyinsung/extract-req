"""채팅 기반 AI 수정 서비스 — claude-agent-sdk 백엔드 (REQ-007).

claude-agent-sdk의 query() API를 사용하여 채팅 수정 요청을 처리한다.
ChatService.chat_stream()과 동일한 SSE 인터페이스 및 PATCH 태그 프로토콜을 준수한다.

SEC-007-02: MAX_MESSAGE_LENGTH 검증을 ChatService와 동일하게 적용한다.
SEC-007-01: ImportError는 호출자가 503으로 변환한다 — 모듈 로드 시 예외를 전파한다.
"""

import json
import re
from typing import AsyncGenerator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

import app.state as state
from app.models.api import ChatMessage
from app.services.chat_service import (
    MAX_MESSAGE_LENGTH,
    _build_system_prompt,
    _process_patches,
)

# PATCH 태그를 실시간 스트리밍에서 제거하기 위한 패턴 (chat_service.py와 동일)
_PATCH_STRIP_RE = re.compile(r"<PATCH>.*?</PATCH>", re.DOTALL)


def _sse(data: dict) -> str:
    """딕셔너리를 SSE 형식 문자열로 직렬화한다."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


class ChatServiceSDK:
    """claude-agent-sdk query()를 통한 채팅 수정 서비스.

    ChatService.chat_stream()과 동일한 SSE 출력 형식 및 PATCH 태그 프로토콜을 유지한다.
    """

    async def chat_stream(
        self, session_id: str, message: str, history: list[ChatMessage]
    ) -> AsyncGenerator[str, None]:
        """채팅 메시지와 히스토리를 받아 claude-agent-sdk 응답을 SSE로 변환한다.

        Args:
            session_id: 현재 세션 ID (상태 조회용)
            message: 사용자 채팅 메시지
            history: 클라이언트가 유지하는 이전 대화 목록

        Yields:
            SSE 형식 문자열 (type: text | patch | done | error)
        """
        # SEC-007-02: 서버 측 메시지 길이 검증 (ChatService와 동일한 상수 재사용)
        if len(message) > MAX_MESSAGE_LENGTH:
            yield _sse({"type": "error", "message": f"메시지는 {MAX_MESSAGE_LENGTH}자를 초과할 수 없습니다."})
            return

        details = state.get_detail()
        if not details:
            yield _sse({"type": "error", "message": "상세요구사항이 없습니다. 먼저 생성해주세요."})
            return

        system_prompt = _build_system_prompt(details)
        # SDK는 멀티턴 messages API를 직접 지원하지 않으므로
        # 히스토리를 단일 프롬프트 문자열로 직렬화하여 전달한다 (설계 문서 트레이드오프 결정)
        full_prompt = _serialize_conversation(system_prompt, history, message)

        try:
            options = ClaudeAgentOptions(
                allowed_tools=[],
                permission_mode="default",
            )

            full_text = ""
            async for sdk_message in query(prompt=full_prompt, options=options):
                if isinstance(sdk_message, AssistantMessage):
                    # 중간 스트리밍 메시지에서 텍스트 추출
                    for block in sdk_message.content:
                        if isinstance(block, TextBlock):
                            chunk = block.text
                            full_text += chunk
                            # PATCH 태그를 제거한 순수 텍스트만 실시간 스트리밍한다
                            clean_chunk = _PATCH_STRIP_RE.sub("", chunk)
                            if clean_chunk:
                                yield _sse({"type": "text", "delta": clean_chunk})
                elif isinstance(sdk_message, ResultMessage):
                    # 최종 결과 메시지 — result 필드에 전체 응답이 있을 수 있다
                    if sdk_message.result and sdk_message.result not in full_text:
                        chunk = sdk_message.result
                        full_text += chunk
                        clean_chunk = _PATCH_STRIP_RE.sub("", chunk)
                        if clean_chunk:
                            yield _sse({"type": "text", "delta": clean_chunk})

            # 스트리밍 완료 후 전체 응답에서 PATCH 태그를 일괄 처리한다
            for event in _process_patches(full_text):
                yield event
            yield _sse({"type": "done"})

        except Exception as e:
            yield _sse({"type": "error", "message": f"오류: {str(e)}"})


def _serialize_conversation(
    system_prompt: str,
    history: list[ChatMessage],
    message: str,
) -> str:
    """시스템 프롬프트와 대화 히스토리, 현재 메시지를 단일 프롬프트 문자열로 직렬화한다.

    claude-agent-sdk는 멀티턴 messages API를 직접 지원하지 않으므로
    텍스트 형식으로 대화 맥락을 포함한다.

    Args:
        system_prompt: 시스템 프롬프트 (상세요구사항 컨텍스트 포함)
        history: 이전 대화 목록
        message: 현재 사용자 메시지

    Returns:
        단일 프롬프트 문자열
    """
    parts = [system_prompt]

    if history:
        parts.append("\n\n[이전 대화]")
        for msg in history:
            role_label = "사용자" if msg.role == "user" else "어시스턴트"
            parts.append(f"{role_label}: {msg.content}")

    parts.append(f"\n\n[현재 요청]\n사용자: {message}")
    return "\n".join(parts)
