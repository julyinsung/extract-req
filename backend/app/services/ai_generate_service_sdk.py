"""AI 상세요구사항 생성 서비스 — claude-agent-sdk 백엔드 (REQ-007).

claude-agent-sdk의 query() API를 사용하여 상세요구사항을 생성한다.
AiGenerateService.generate_stream()과 동일한 SSE 인터페이스를 준수한다.

SEC-007-05: 원본 요구사항을 JSON 직렬화하여 전달 — 프롬프트 인젝션 방지.
SEC-007-01: ImportError는 호출자가 503으로 변환한다 — 모듈 로드 시 예외를 전파한다.
"""

import json
from typing import AsyncGenerator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

import app.state as state
from app.models.requirement import DetailRequirement
from app.services.ai_generate_service import (
    _SYSTEM_PROMPT,
    _find_obj_end,
    _parse_obj,
)


def _sse(data: dict) -> str:
    """딕셔너리를 SSE 형식 문자열로 직렬화한다."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


class AIGenerateServiceSDK:
    """claude-agent-sdk query()를 통한 상세요구사항 생성 서비스.

    AiGenerateService.generate_stream()과 동일한 SSE 출력 형식을 유지한다.
    """

    async def generate_stream(self, session_id: str) -> AsyncGenerator[str, None]:
        """원본 요구사항을 claude-agent-sdk로 상세요구사항으로 분해하여 SSE 스트림으로 발행한다.

        스트리밍 청크를 누적하다가 완전한 JSON 객체 경계를 감지하면 즉시 파싱·발행한다.
        완료 후 state에 전체 목록을 저장한다.

        Args:
            session_id: 클라이언트 세션 식별자 (state 조회에만 사용)

        Yields:
            SSE 형식 문자열 — type이 "item", "done", "error" 중 하나
        """
        originals = state.get_original()
        if not originals:
            yield _sse({"type": "error", "message": "파싱된 요구사항이 없습니다."})
            return

        # SEC-007-05: JSON 직렬화로 전달 — content 내 임의 지시문이 프롬프트에 병합되는 것을 차단
        user_message = (
            "다음 원본 요구사항 목록을 상세요구사항으로 분해해주세요.\n"
            + json.dumps([r.model_dump() for r in originals], ensure_ascii=False)
        )
        full_prompt = f"{_SYSTEM_PROMPT}\n\n{user_message}"

        details: list[DetailRequirement] = []
        order_counters: dict[str, int] = {}
        buf = ""

        try:
            options = ClaudeAgentOptions(
                allowed_tools=[],
                permission_mode="default",
            )

            async for message in query(prompt=full_prompt, options=options):
                if isinstance(message, AssistantMessage):
                    # 중간 스트리밍 메시지에서 텍스트 추출
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            buf += block.text
                            # 완전한 JSON 객체가 나올 때마다 즉시 파싱하여 item 이벤트 발행
                            while True:
                                start = buf.find("{")
                                if start == -1:
                                    break
                                end = _find_obj_end(buf, start)
                                if end == -1:
                                    break
                                obj_str = buf[start : end + 1]
                                buf = buf[end + 1 :]
                                event = _parse_obj(obj_str, order_counters, details)
                                if event:
                                    yield event
                elif isinstance(message, ResultMessage):
                    # 최종 결과 메시지 — 남은 버퍼를 처리한다
                    if message.result:
                        buf += message.result
                    while True:
                        start = buf.find("{")
                        if start == -1:
                            break
                        end = _find_obj_end(buf, start)
                        if end == -1:
                            break
                        obj_str = buf[start : end + 1]
                        buf = buf[end + 1 :]
                        event = _parse_obj(obj_str, order_counters, details)
                        if event:
                            yield event

            state.set_detail(details)
            yield _sse({"type": "done", "total": len(details)})

        except Exception as e:
            yield _sse({"type": "error", "message": f"생성 실패: {str(e)}"})
