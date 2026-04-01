"""채팅 기반 AI 수정 서비스 (REQ-004).

Claude API 스트리밍 응답에서 <PATCH> 태그를 감지하여 상세요구사항을 수정한다.
서버는 채팅 히스토리를 저장하지 않고, 클라이언트가 매 요청마다 전달한다.
"""

import json
import os
import re
from typing import AsyncGenerator

from anthropic import AsyncAnthropic, APIError

from app.models.api import ChatMessage
import app.state as state

# PATCH 태그 전체를 추출하는 패턴 — 완료 후 일괄 처리에 사용한다
PATCH_RE = re.compile(r"<PATCH>(.*?)</PATCH>", re.DOTALL)

# SEC-004-02: 채팅 메시지 서버 측 길이 제한 (2000자)
MAX_MESSAGE_LENGTH = 2000


class ChatService:
    """채팅 메시지와 현재 상세요구사항 컨텍스트를 결합하여 Claude API를 호출하고 SSE로 반환한다."""

    def __init__(self):
        self.client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    async def chat_stream(
        self, session_id: str, message: str, history: list[ChatMessage]
    ) -> AsyncGenerator[str, None]:
        """채팅 메시지와 히스토리를 받아 Claude API 스트리밍 응답을 SSE로 변환한다.

        Args:
            session_id: 현재 세션 ID (상태 조회용)
            message: 사용자 채팅 메시지
            history: 클라이언트가 유지하는 이전 대화 목록

        Yields:
            SSE 형식 문자열 (type: text | patch | done | error)
        """
        # SEC-004-02: 서버 측 메시지 길이 검증
        if len(message) > MAX_MESSAGE_LENGTH:
            yield _sse({"type": "error", "message": f"메시지는 {MAX_MESSAGE_LENGTH}자를 초과할 수 없습니다."})
            return

        details = state.get_detail()
        if not details:
            yield _sse({"type": "error", "message": "상세요구사항이 없습니다. 먼저 생성해주세요."})
            return

        system_prompt = _build_system_prompt(details)
        messages = _build_messages(history, message)

        try:
            full_text = ""
            async with self.client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for chunk in stream.text_stream:
                    full_text += chunk
                    # PATCH 태그를 제거한 순수 텍스트만 스트리밍한다
                    clean_chunk = re.sub(r"<PATCH>.*?</PATCH>", "", chunk, flags=re.DOTALL)
                    if clean_chunk:
                        yield _sse({"type": "text", "delta": clean_chunk})

            # 스트리밍 완료 후 전체 응답에서 PATCH 태그를 일괄 처리한다
            # async 함수에서 yield from은 사용 불가 — 명시적 루프로 대체한다
            for event in _process_patches(full_text):
                yield event
            yield _sse({"type": "done"})

        except APIError as e:
            yield _sse({"type": "error", "message": f"Claude API 오류: {str(e)}"})
        except Exception as e:
            yield _sse({"type": "error", "message": f"오류: {str(e)}"})


def _build_system_prompt(details: list) -> str:
    """현재 상세요구사항 목록을 포함한 시스템 프롬프트를 조립한다.

    상세요구사항 전체를 JSON으로 직렬화하여 Claude가 수정 대상을 정확히 파악할 수 있게 한다.
    """
    details_json = json.dumps([d.model_dump() for d in details], ensure_ascii=False)
    return f"""당신은 요구사항 분석 전문가입니다.
현재 상세요구사항 목록:
{details_json}

수정 요청 시 두 가지를 함께 반환하세요:
1. 채팅 응답 텍스트 (설명)
2. 수정 명령: <PATCH>{{"id":"...","field":"name|content|category","value":"..."}}</PATCH>

수정 없는 일반 질문은 PATCH 태그 없이 텍스트만 반환하세요."""


def _build_messages(history: list[ChatMessage], message: str) -> list[dict]:
    """채팅 히스토리와 현재 메시지를 Claude API messages 형식으로 변환한다."""
    messages = [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": message})
    return messages


def _process_patches(full_text: str):
    """전체 응답 텍스트에서 PATCH 태그를 파싱하여 state에 반영하고 patch 이벤트를 생성한다.

    JSON 파싱 실패 시 해당 태그를 조용히 건너뛴다 — 부분 오류가 전체 응답을 차단하지 않도록 한다.
    """
    for match in PATCH_RE.finditer(full_text):
        try:
            patch = json.loads(match.group(1))
            req_id = patch.get("id", "")
            field = patch.get("field", "")
            value = patch.get("value", "")
            if req_id and field and value:
                state.patch_detail(req_id, field, value)
                yield _sse({"type": "patch", "id": req_id, "field": field, "value": value})
        except json.JSONDecodeError:
            pass


def _sse(data: dict) -> str:
    """딕셔너리를 SSE 형식 문자열로 직렬화한다."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
