"""AI 상세요구사항 생성 서비스.

Claude API를 SSE 스트리밍으로 호출하여 원본 요구사항을 상세요구사항으로 분해한다.
SEC-002-01: ANTHROPIC_API_KEY는 환경변수에서만 로드하며 코드에 하드코딩 금지.
SEC-002-02: 원본 요구사항 content를 JSON 직렬화하여 전달 — 프롬프트 인젝션 방지.
"""

import json
import os
from typing import AsyncGenerator

from anthropic import AsyncAnthropic, APIError

import app.state as state
from app.models.requirement import DetailRequirement


# 시스템 프롬프트 — 변경 시 req-002-design.md 프롬프트 전략 섹션을 함께 갱신해야 한다
_SYSTEM_PROMPT = """당신은 공공/기업 제안 업무 전문가입니다.
주어진 원본 요구사항을 구현 가능한 상세요구사항으로 분해하세요.

출력 규칙:
- JSON 배열만 반환 (마크다운 코드 블록, 설명 텍스트 없이 순수 JSON)
- 각 항목: {"id": "...", "parent_id": "...", "category": "...", "name": "...", "content": "..."}
- 원본 ID가 "SFR-001"이면 상세 ID는 "SFR-001-01", "SFR-001-02" ...
- 원본 1건당 2~5개의 구현 단위로 분해"""

_CLAUDE_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 8192


class AiGenerateService:
    """Claude API 스트리밍을 통한 상세요구사항 생성 서비스."""

    def __init__(self):
        # SEC-002-01: API 키를 환경변수에서 주입
        self.client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    async def generate_stream(self, session_id: str) -> AsyncGenerator[str, None]:
        """원본 요구사항을 Claude API로 상세요구사항으로 분해하여 SSE 스트림으로 발행한다.

        스트리밍 청크를 누적하다가 완전한 JSON 객체 경계를 감지하면 즉시 파싱·발행한다.
        완료 후 state에 전체 목록을 저장한다.

        Args:
            session_id: 클라이언트 세션 식별자 (현재 인메모리 싱글턴이므로 조회에만 사용)

        Yields:
            SSE 형식 문자열 — type이 "item", "done", "error" 중 하나
        """
        originals = state.get_original()
        if not originals:
            yield _sse({"type": "error", "message": "파싱된 요구사항이 없습니다."})
            return

        # SEC-002-02: JSON 직렬화로 전달하여 content 내 임의 지시문이 프롬프트에 병합되는 것을 차단
        user_message = (
            "다음 원본 요구사항 목록을 상세요구사항으로 분해해주세요.\n"
            + json.dumps([r.model_dump() for r in originals], ensure_ascii=False)
        )

        details: list[DetailRequirement] = []
        buf = ""
        # parent_id별 생성 순서를 추적하여 ID 채번 보정에 사용
        order_counters: dict[str, int] = {}

        try:
            async with self.client.messages.stream(
                model=_CLAUDE_MODEL,
                max_tokens=_MAX_TOKENS,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                async for chunk in stream.text_stream:
                    buf += chunk
                    # 완전한 JSON 객체가 나올 때마다 즉시 파싱하여 item 이벤트 발행
                    while True:
                        start = buf.find("{")
                        if start == -1:
                            break
                        end = _find_obj_end(buf, start)
                        if end == -1:
                            # 아직 객체가 완전하지 않으면 다음 청크까지 대기
                            break
                        obj_str = buf[start : end + 1]
                        buf = buf[end + 1 :]
                        event = _parse_obj(obj_str, order_counters, details)
                        if event:
                            yield event

            state.set_detail(details)
            yield _sse({"type": "done", "total": len(details)})

        except APIError as e:
            yield _sse({"type": "error", "message": f"Claude API 오류: {str(e)}"})
        except Exception as e:
            yield _sse({"type": "error", "message": f"생성 실패: {str(e)}"})


def _parse_obj(
    obj_str: str,
    order_counters: dict[str, int],
    details: list[DetailRequirement],
) -> str | None:
    """JSON 객체 문자열을 DetailRequirement로 변환하고 SSE item 이벤트를 반환한다.

    parent_id가 없거나 JSON 파싱 실패 시 None을 반환하여 조용히 건너뛴다.
    id가 없거나 형식 불일치 시 parent_id + 시퀀스로 서버 채번하여 보정한다.

    Args:
        obj_str: 완전한 JSON 객체 문자열
        order_counters: parent_id별 순서 카운터 (in-place 수정)
        details: 생성된 DetailRequirement 누적 목록 (in-place 수정)

    Returns:
        SSE item 이벤트 문자열, 파싱 불가 시 None
    """
    try:
        obj = json.loads(obj_str)
    except json.JSONDecodeError:
        return None

    # parent_id가 없으면 채번 불가 — 건너뜀. id는 없어도 서버에서 보정한다
    if "parent_id" not in obj:
        return None

    parent_id = obj["parent_id"]
    count = order_counters.get(parent_id, 0)
    # AI가 제공한 id가 누락되면 {parent_id}-NN 규칙으로 서버에서 채번
    obj_id = obj.get("id") or f"{parent_id}-{count + 1:02d}"

    detail = DetailRequirement(
        id=obj_id,
        parent_id=parent_id,
        category=obj.get("category", ""),
        name=obj.get("name", ""),
        content=obj.get("content", ""),
        order_index=count,
    )
    order_counters[parent_id] = count + 1
    details.append(detail)
    return _sse({"type": "item", "data": detail.model_dump()})


def _sse(data: dict) -> str:
    """딕셔너리를 SSE 형식 문자열로 직렬화한다.

    클라이언트가 ReadableStream으로 수신할 수 있도록 'data: ...\\n\\n' 형식을 준수한다.
    """
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _find_obj_end(s: str, start: int) -> int:
    """중첩 괄호와 문자열 이스케이프를 고려하여 JSON 객체의 닫힘 위치를 반환한다.

    스트리밍 청크가 객체 중간에서 잘릴 수 있으므로, 완전한 객체가 없으면 -1을 반환한다.

    Args:
        s: 탐색 대상 문자열
        start: '{' 문자의 시작 인덱스

    Returns:
        대응하는 '}' 인덱스, 없으면 -1
    """
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(s)):
        c = s[i]
        if escape:
            escape = False
            continue
        if c == "\\" and in_str:
            escape = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1
