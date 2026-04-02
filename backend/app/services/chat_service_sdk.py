"""채팅 기반 AI 수정 서비스 — claude-agent-sdk 백엔드 (REQ-007).

claude-agent-sdk의 query() API를 사용하여 채팅 수정 요청을 처리한다.
ChatService.chat_stream()과 동일한 SSE 인터페이스 및 PATCH 태그 프로토콜을 준수한다.

SEC-007-02: MAX_MESSAGE_LENGTH 검증을 ChatService와 동일하게 적용한다.
SEC-007-01: ImportError는 호출자가 503으로 변환한다 — 모듈 로드 시 예외를 전파한다.

Windows 호환성:
  ai_generate_service_sdk.py의 _run_sdk_in_thread / _SENTINEL 패턴을 동일하게 적용한다.
"""

import asyncio
import json
import re
import shutil
import sys
import threading
from queue import Queue
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
    _TAG_STRIP_RE,
    _build_system_prompt,
    _process_patches,
    _process_replace,
)
_SENTINEL = object()


def _sse(data: dict) -> str:
    """딕셔너리를 SSE 형식 문자열로 직렬화한다."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _run_sdk_in_thread(full_prompt: str, options: ClaudeAgentOptions, result_queue: "Queue") -> None:
    """별도 스레드에서 ProactorEventLoop를 생성하여 SDK query를 실행한다."""
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _collect():
        try:
            async for msg in query(prompt=full_prompt, options=options):
                result_queue.put(msg)
        except Exception as exc:
            result_queue.put(exc)
        finally:
            result_queue.put(_SENTINEL)

    try:
        loop.run_until_complete(_collect())
    finally:
        loop.close()


class ChatServiceSDK:
    """claude-agent-sdk query()를 통한 채팅 수정 서비스.

    ChatService.chat_stream()과 동일한 SSE 출력 형식 및 PATCH 태그 프로토콜을 유지한다.
    """

    async def chat_stream(
        self, session_id: str, message: str, history: list[ChatMessage], req_group: str
    ) -> AsyncGenerator[str, None]:
        """채팅 메시지와 히스토리를 받아 claude-agent-sdk 응답을 SSE로 변환한다.

        Args:
            session_id: 현재 세션 ID (상태 조회용)
            message: 사용자 채팅 메시지
            history: 클라이언트가 유지하는 이전 대화 목록
            req_group: 선택된 REQ 그룹 ID — 컨텍스트 필터링에 사용 (REQ-004-05)

        Yields:
            SSE 형식 문자열 (type: text | patch | replace | done | error)
        """
        # SEC-007-02: 서버 측 메시지 길이 검증 (ChatService와 동일한 상수 재사용)
        if len(message) > MAX_MESSAGE_LENGTH:
            yield _sse({"type": "error", "message": f"메시지는 {MAX_MESSAGE_LENGTH}자를 초과할 수 없습니다."})
            return

        # REQ-004-05: 선택된 그룹의 원본+상세항목만 컨텍스트로 사용
        original_req = state.get_original_by_group(req_group)
        if original_req is None:
            yield _sse({"type": "error", "message": f"원본 요구사항을 찾을 수 없습니다: {req_group}"})
            return

        filtered_details = state.get_detail_by_group(req_group)
        system_prompt = _build_system_prompt(original_req, filtered_details)
        full_prompt = _serialize_conversation(system_prompt, history, message)

        try:
            cli_path = shutil.which("claude")
            # REQ-009-02: 저장된 sdk_session_id가 있으면 동일 세션을 이어받는다.
            sdk_session_id = state.get_sdk_session_id(req_group)
            if sdk_session_id:
                options = ClaudeAgentOptions(
                    allowed_tools=[],
                    permission_mode="default",
                    cli_path=cli_path,
                    resume=sdk_session_id,
                )
            else:
                options = ClaudeAgentOptions(
                    allowed_tools=[],
                    permission_mode="default",
                    cli_path=cli_path,
                )

            # Windows SelectorEventLoop 우회: 별도 스레드의 ProactorEventLoop에서 SDK 실행
            result_queue: Queue = Queue()
            thread = threading.Thread(
                target=_run_sdk_in_thread,
                args=(full_prompt, options, result_queue),
                daemon=True,
            )
            thread.start()

            full_text = ""
            while True:
                sdk_message = await asyncio.to_thread(result_queue.get)

                if sdk_message is _SENTINEL:
                    break
                if isinstance(sdk_message, Exception):
                    raise sdk_message

                if isinstance(sdk_message, AssistantMessage):
                    for block in sdk_message.content:
                        if isinstance(block, TextBlock):
                            chunk = block.text
                            full_text += chunk
                            clean_chunk = _TAG_STRIP_RE.sub("", chunk)
                            if clean_chunk:
                                yield _sse({"type": "text", "delta": clean_chunk})
                elif isinstance(sdk_message, ResultMessage):
                    if sdk_message.result and sdk_message.result not in full_text:
                        chunk = sdk_message.result
                        full_text += chunk
                        clean_chunk = _TAG_STRIP_RE.sub("", chunk)
                        if clean_chunk:
                            yield _sse({"type": "text", "delta": clean_chunk})

            # 스트리밍 완료 후 전체 응답에서 PATCH → REPLACE 순으로 일괄 처리한다
            for event in _process_patches(full_text):
                yield event
            for event in _process_replace(full_text, req_group):
                yield event
            yield _sse({"type": "done"})

        except Exception as e:
            yield _sse({"type": "error", "message": f"오류: {str(e)}"})


def _serialize_conversation(
    system_prompt: str,
    history: list[ChatMessage],
    message: str,
) -> str:
    """시스템 프롬프트와 대화 히스토리, 현재 메시지를 단일 프롬프트 문자열로 직렬화한다."""
    parts = [system_prompt]

    if history:
        parts.append("\n\n[이전 대화]")
        for msg in history:
            role_label = "사용자" if msg.role == "user" else "어시스턴트"
            parts.append(f"{role_label}: {msg.content}")

    parts.append(f"\n\n[현재 요청]\n사용자: {message}")
    return "\n".join(parts)
