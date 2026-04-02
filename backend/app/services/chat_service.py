"""채팅 기반 AI 수정 서비스 (REQ-004).

Claude API 스트리밍 응답에서 <PATCH> 태그와 <REPLACE> 태그를 감지하여 상세요구사항을 수정한다.
서버는 채팅 히스토리를 저장하지 않고, 클라이언트가 매 요청마다 전달한다.
REQ-004-05: req_group으로 컨텍스트를 선택된 그룹으로 제한한다.
REQ-004-06: REPLACE 태그 감지 시 그룹 전체 항목을 교체하는 replace SSE 이벤트를 발행한다.
"""

import json
import os
import re
from typing import AsyncGenerator

from app.models.api import ChatMessage
from app.models.requirement import DetailRequirement, OriginalRequirement
import app.state as state

# PATCH 태그 전체를 추출하는 패턴 — 완료 후 일괄 처리에 사용한다
PATCH_RE = re.compile(r"<PATCH>(.*?)</PATCH>", re.DOTALL)

# REPLACE 태그 전체를 추출하는 패턴 — 완료 후 일괄 처리에 사용한다
REPLACE_RE = re.compile(r"<REPLACE>(.*?)</REPLACE>", re.DOTALL)

# 실시간 스트리밍에서 PATCH/REPLACE 태그를 제거하기 위한 패턴
_TAG_STRIP_RE = re.compile(r"<(?:PATCH|REPLACE)>.*?</(?:PATCH|REPLACE)>", re.DOTALL)

# SEC-004-02: 채팅 메시지 서버 측 길이 제한 (2000자)
MAX_MESSAGE_LENGTH = 2000


class ChatService:
    """채팅 메시지와 현재 상세요구사항 컨텍스트를 결합하여 Claude API를 호출하고 SSE로 반환한다."""

    def __init__(self):
        # 지연 import — anthropic 패키지가 없는 환경에서 순수 유틸 함수(_process_replace 등)의 import를 허용한다.
        # 테스트에서 client를 mock으로 교체하므로 초기화 실패 시 None으로 설정한다.
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        except ImportError:
            self.client = None  # type: ignore[assignment]

    async def chat_stream(
        self, session_id: str, message: str, history: list[ChatMessage], req_group: str
    ) -> AsyncGenerator[str, None]:
        """채팅 메시지와 히스토리를 받아 Claude API 스트리밍 응답을 SSE로 변환한다.

        Args:
            session_id: 현재 세션 ID (상태 조회용)
            message: 사용자 채팅 메시지
            history: 클라이언트가 유지하는 이전 대화 목록
            req_group: 선택된 REQ 그룹 ID — 컨텍스트 필터링에 사용 (REQ-004-05)

        Yields:
            SSE 형식 문자열 (type: text | patch | replace | done | error)
        """
        # SEC-004-02: 서버 측 메시지 길이 검증
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
                    # PATCH/REPLACE 태그를 제거한 순수 텍스트만 스트리밍한다
                    clean_chunk = _TAG_STRIP_RE.sub("", chunk)
                    if clean_chunk:
                        yield _sse({"type": "text", "delta": clean_chunk})

            # 스트리밍 완료 후 전체 응답에서 PATCH → REPLACE 순으로 일괄 처리한다
            # async 함수에서 yield from은 사용 불가 — 명시적 루프로 대체한다
            for event in _process_patches(full_text):
                yield event
            for event in _process_replace(full_text, req_group):
                yield event
            yield _sse({"type": "done"})

        except Exception as e:
            # anthropic.APIError는 Exception을 상속하므로 공통 핸들링 가능
            yield _sse({"type": "error", "message": f"오류: {str(e)}"})


def _build_system_prompt(
    original_req: OriginalRequirement | None, filtered_details: list
) -> str:
    """선택된 REQ 그룹의 원본 요구사항과 상세항목만 포함한 시스템 프롬프트를 조립한다.

    Args:
        original_req: 선택된 그룹의 원본 요구사항 1건 (없으면 None)
        filtered_details: 해당 그룹의 상세요구사항 목록

    REQ-004-05: 다른 그룹의 상세항목을 포함하지 않아 컨텍스트를 정확히 제한한다.
    """
    original_text = ""
    if original_req is not None:
        original_text = f"원본 요구사항:\n{json.dumps(original_req.model_dump(), ensure_ascii=False)}\n\n"

    details_json = json.dumps([d.model_dump() for d in filtered_details], ensure_ascii=False)
    return f"""당신은 요구사항 분석 전문가입니다.
{original_text}현재 상세요구사항 목록:
{details_json}

수정 요청 시 두 가지 방식 중 하나를 선택하세요 (동시 사용 금지):

방식 1 — 개별 수정 (PATCH):
<PATCH>{{"id":"...","field":"name|content|category","value":"..."}}</PATCH>

방식 2 — 전체 교체 (REPLACE, 대규모 재작성 시):
<REPLACE>[
  {{"name":"...","content":"...","category":"..."}},
  {{"name":"...","content":"...","category":"..."}}
]</REPLACE>

수정 없는 일반 질문은 태그 없이 텍스트만 반환하세요."""


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


def _process_replace(full_text: str, req_group: str):
    """전체 응답 텍스트에서 REPLACE 태그를 파싱하여 그룹 전체를 교체하고 replace 이벤트를 생성한다.

    Args:
        full_text: 스트리밍 완료 후 누적된 전체 응답 텍스트
        req_group: 교체 대상 REQ 그룹 ID

    Yields:
        replace SSE 이벤트 문자열 (교체 성공 시에만 발행)

    REPLACE와 PATCH는 동시에 사용하지 않도록 AI 프롬프트에서 제한하나,
    JSON 파싱 실패 시 해당 교체를 조용히 건너뛴다 — PATCH와 동일한 에러 정책.
    REQ-004-06: 교체 성공 시 state.replace_detail_group()을 호출하고 replace 이벤트를 발행한다.
    """
    for match in REPLACE_RE.finditer(full_text):
        try:
            items_data = json.loads(match.group(1))
            if not isinstance(items_data, list):
                continue

            # 그룹 번호 추출: "REQ-001" → "001"
            group_num = req_group.split("-")[-1] if "-" in req_group else req_group

            new_items: list[DetailRequirement] = []
            for idx, item in enumerate(items_data):
                if not isinstance(item, dict):
                    continue
                new_id = f"{req_group}-{idx + 1:02d}"
                detail = DetailRequirement(
                    id=new_id,
                    parent_id=req_group,
                    name=item.get("name", ""),
                    content=item.get("content", ""),
                    category=item.get("category", ""),
                    order_index=idx,
                    is_modified=True,
                )
                new_items.append(detail)

            if not new_items:
                continue

            state.replace_detail_group(req_group, new_items)
            yield _sse({
                "type": "replace",
                "req_group": req_group,
                "items": [item.model_dump() for item in new_items],
            })
        except (json.JSONDecodeError, Exception):
            # JSON 파싱 오류 또는 기타 오류 시 건너뜀 — 스트림 비중단
            pass


def _sse(data: dict) -> str:
    """딕셔너리를 SSE 형식 문자열로 직렬화한다."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
