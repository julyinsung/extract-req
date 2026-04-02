"""AI 상세요구사항 생성 서비스 — claude-agent-sdk 백엔드 (REQ-007).

claude-agent-sdk의 query() API를 사용하여 상세요구사항을 생성한다.
AiGenerateService.generate_stream()과 동일한 SSE 인터페이스를 준수한다.

SEC-007-05: 원본 요구사항을 JSON 직렬화하여 전달 — 프롬프트 인젝션 방지.
SEC-007-01: ImportError는 호출자가 503으로 변환한다 — 모듈 로드 시 예외를 전파한다.

Windows 호환성 주의:
  uvicorn(0.42+)은 Windows에서 SelectorEventLoop를 사용한다.
  SelectorEventLoop는 asyncio.create_subprocess_exec를 지원하지 않아
  claude-agent-sdk가 CLIConnectionError(NotImplementedError)를 발생시킨다.
  이를 해결하기 위해 SDK 호출을 별도 스레드의 ProactorEventLoop에서 실행하고,
  결과를 스레드 안전 Queue를 통해 메인 이벤트 루프로 전달한다.
"""

import asyncio
import json
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
from app.models.requirement import DetailRequirement
from app.services.ai_generate_service import (
    _SYSTEM_PROMPT,
    _find_obj_end,
    _parse_obj,
)

_SENTINEL = object()  # 스레드 종료 시그널


def _sse(data: dict) -> str:
    """딕셔너리를 SSE 형식 문자열로 직렬화한다."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _run_sdk_in_thread(full_prompt: str, options: ClaudeAgentOptions, result_queue: "Queue") -> None:
    """별도 스레드에서 ProactorEventLoop를 생성하여 SDK query를 실행한다.

    Windows의 SelectorEventLoop에서는 subprocess 생성이 불가하므로
    스레드별 ProactorEventLoop를 사용한다.
    결과 메시지(또는 예외)를 result_queue에 넣고, 완료 시 _SENTINEL을 넣는다.

    Args:
        full_prompt: SDK에 전달할 전체 프롬프트
        options: ClaudeAgentOptions 인스턴스
        result_queue: 메시지 전달용 스레드 안전 큐
    """
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


class AIGenerateServiceSDK:
    """claude-agent-sdk query()를 통한 상세요구사항 생성 서비스.

    AiGenerateService.generate_stream()과 동일한 SSE 출력 형식을 유지한다.
    """

    async def generate_stream(self, session_id: str, req_group: str = "") -> AsyncGenerator[str, None]:
        """원본 요구사항을 claude-agent-sdk로 상세요구사항으로 분해하여 SSE 스트림으로 발행한다.

        스트리밍 청크를 누적하다가 완전한 JSON 객체 경계를 감지하면 즉시 파싱·발행한다.
        완료 후 state에 전체 목록을 저장한다.
        parent_id 그룹 완료 시 progress 이벤트를 발행한다 (REQ-010-01).

        Args:
            session_id: 클라이언트 세션 식별자 (state 조회에만 사용)
            req_group: 생성 완료 후 SDK session_id를 저장할 REQ 그룹 ID (REQ-009)

        Yields:
            SSE 형식 문자열 — type이 "item", "progress", "done", "error" 중 하나
        """
        originals = state.get_original()
        if not originals:
            yield _sse({"type": "error", "message": "파싱된 요구사항이 없습니다."})
            return

        total_originals = len(originals)

        # SEC-007-05: JSON 직렬화로 전달 — content 내 임의 지시문이 프롬프트에 병합되는 것을 차단
        user_message = (
            "다음 원본 요구사항 목록을 상세요구사항으로 분해해주세요.\n"
            + json.dumps([r.model_dump() for r in originals], ensure_ascii=False)
        )
        full_prompt = f"{_SYSTEM_PROMPT}\n\n{user_message}"

        details: list[DetailRequirement] = []
        order_counters: dict[str, int] = {}
        buf = ""
        # progress 추적: 완료된 parent_id 집합 및 마지막 처리 parent_id
        completed_parents: set[str] = set()
        last_parent_id: str | None = None

        try:
            # cli_path: PATH 환경에 무관하게 claude 바이너리를 명시적으로 지정 (SEC-007-04)
            cli_path = shutil.which("claude")
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

            while True:
                # 큐에서 메시지를 가져오는 동안 이벤트 루프를 블로킹하지 않도록 to_thread 사용
                message = await asyncio.to_thread(result_queue.get)

                if message is _SENTINEL:
                    break
                if isinstance(message, Exception):
                    raise message

                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            buf += block.text
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
                                    # REQ-010-01: parent_id 전환 감지 시 이전 그룹 progress 발행
                                    if details:
                                        current_parent = details[-1].parent_id
                                        if last_parent_id is not None and last_parent_id != current_parent:
                                            if last_parent_id not in completed_parents:
                                                completed_parents.add(last_parent_id)
                                                yield _sse({
                                                    "type": "progress",
                                                    "current": len(completed_parents),
                                                    "total": total_originals,
                                                    "req_id": last_parent_id,
                                                })
                                        last_parent_id = current_parent
                elif isinstance(message, ResultMessage):
                    # ResultMessage.result는 AssistantMessage 청크의 전체본이므로 buf에 추가하지 않는다.
                    # buf에 남아있는 불완전한 청크(마지막 JSON이 잘린 경우)만 처리한다.
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
                            if details:
                                last_parent_id = details[-1].parent_id
                    # REQ-009-01: SDK 실행 완전 종료 시점에 session_id를 그룹 키로 저장한다.
                    # req_group이 비어있으면 저장 건너뜀 — 기존 동작(새 세션) 유지.
                    sdk_sid = getattr(message, "session_id", None)
                    if sdk_sid and req_group:
                        state.set_sdk_session_id(req_group, sdk_sid)
                    elif not sdk_sid:
                        import logging
                        logging.getLogger(__name__).warning(
                            "ResultMessage에 session_id가 없습니다. 세션 연속성 비활성화."
                        )

            # 마지막 parent_id progress 발행 (전환이 없었을 경우 포함)
            if last_parent_id and last_parent_id not in completed_parents:
                completed_parents.add(last_parent_id)
                yield _sse({
                    "type": "progress",
                    "current": len(completed_parents),
                    "total": total_originals,
                    "req_id": last_parent_id,
                })

            state.set_detail(details)
            yield _sse({"type": "done", "total": len(details)})

        except Exception as e:
            yield _sse({"type": "error", "message": f"생성 실패: {str(e)}"})
