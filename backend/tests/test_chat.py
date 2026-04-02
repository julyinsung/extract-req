"""채팅 서비스 단위 테스트.

UT-004-01: 정상 요청 → text/patch 이벤트 발행
UT-004-02: PATCH 태그 파싱 → patch 이벤트 + state.patch_detail() 호출 확인
UT-004-03: 일반 질문 → text 이벤트만 발행, patch 없음
UT-004-04: Claude APIError → error 이벤트 발행

실제 Claude API를 호출하지 않고 AsyncMock으로 스트리밍 응답을 모의한다.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# anthropic 패키지가 없는 환경에서는 이 테스트 모듈 전체를 스킵한다
pytest.importorskip("anthropic", reason="anthropic 패키지 필요 — 설치 없으면 스킵")

import app.state as state
from app.models.requirement import DetailRequirement, OriginalRequirement
from app.services.chat_service import ChatService, _sse


# ---------------------------------------------------------------------------
# 픽스처
# ---------------------------------------------------------------------------


_REQ_GROUP = "SFR-001"  # 테스트에서 사용하는 req_group 상수


def _make_originals() -> list[OriginalRequirement]:
    """테스트용 원본 요구사항 픽스처."""
    return [
        OriginalRequirement(
            id="SFR-001",
            category="기능요구사항",
            name="파일 업로드",
            content="사용자는 HWP 파일을 업로드할 수 있다.",
            order_index=0,
        )
    ]


def _make_details() -> list[DetailRequirement]:
    """테스트용 상세요구사항 픽스처."""
    return [
        DetailRequirement(
            id="SFR-001-01",
            parent_id="SFR-001",
            category="기능요구사항",
            name="파일 업로드 UI",
            content="드래그앤드롭으로 파일을 업로드한다.",
            order_index=0,
        ),
        DetailRequirement(
            id="SFR-001-02",
            parent_id="SFR-001",
            category="기능요구사항",
            name="파일 유효성 검사",
            content="HWP 형식만 허용한다.",
            order_index=1,
        ),
    ]


def _build_mock_stream(chunks: list[str]):
    """text_stream async generator를 흉내 내는 mock 컨텍스트 매니저를 반환한다.

    ChatService가 async with stream: 패턴으로 사용하므로 __aenter__/__aexit__를 구현한다.
    """

    async def _text_stream():
        for chunk in chunks:
            yield chunk

    mock_stream = MagicMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=False)
    mock_stream.text_stream = _text_stream()
    return mock_stream


def _parse_events(events: list[str]) -> list[dict]:
    """SSE 이벤트 문자열 목록을 dict 목록으로 파싱한다."""
    result = []
    for e in events:
        raw = e.removeprefix("data: ").strip()
        if raw:
            result.append(json.loads(raw))
    return result


# ---------------------------------------------------------------------------
# UT-004-01: 정상 요청 → text/patch 이벤트 발행
# ---------------------------------------------------------------------------


class TestChatStreamNormal:
    """UT-004-01: 정상 요청 시 text와 patch 이벤트가 발행되어야 한다."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())
        state.set_detail(_make_details())

    @pytest.mark.asyncio
    async def test_text_and_patch_events_emitted(self):
        """PATCH 태그가 포함된 응답 → text 이벤트와 patch 이벤트가 모두 발행되어야 한다."""
        patch_json = json.dumps(
            {"id": "SFR-001-01", "field": "content", "value": "수정된 내용"}
        )
        response_chunks = [
            "요청하신 내용을 수정했습니다. ",
            f"<PATCH>{patch_json}</PATCH>",
        ]
        mock_stream = _build_mock_stream(response_chunks)

        service = ChatService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            events = []
            async for event in service.chat_stream("test-session", "수정해줘", [], _REQ_GROUP):
                events.append(event)

        parsed = _parse_events(events)
        types = [e["type"] for e in parsed]

        assert "text" in types, "text 이벤트가 발행되어야 한다"
        assert "patch" in types, "patch 이벤트가 발행되어야 한다"
        assert "done" in types, "done 이벤트가 발행되어야 한다"

    @pytest.mark.asyncio
    async def test_done_event_is_last(self):
        """done 이벤트가 마지막으로 발행되어야 한다."""
        mock_stream = _build_mock_stream(["안녕하세요."])

        service = ChatService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            events = []
            async for event in service.chat_stream("test-session", "안녕", [], _REQ_GROUP):
                events.append(event)

        parsed = _parse_events(events)
        assert parsed[-1]["type"] == "done", "마지막 이벤트가 done이어야 한다"


# ---------------------------------------------------------------------------
# UT-004-02: PATCH 태그 파싱 → patch 이벤트 + state.patch_detail() 호출
# ---------------------------------------------------------------------------


class TestPatchParsing:
    """UT-004-02: <PATCH> 태그가 파싱되어 patch 이벤트 발행과 state 업데이트가 이루어져야 한다."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())
        state.set_detail(_make_details())

    @pytest.mark.asyncio
    async def test_patch_event_contains_correct_fields(self):
        """patch 이벤트에 id, field, value가 포함되어야 한다."""
        patch_json = json.dumps(
            {"id": "SFR-001-01", "field": "content", "value": "새로운 내용"}
        )
        mock_stream = _build_mock_stream([f"<PATCH>{patch_json}</PATCH>"])

        service = ChatService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            events = []
            async for event in service.chat_stream("test-session", "수정", [], _REQ_GROUP):
                events.append(event)

        parsed = _parse_events(events)
        patch_events = [e for e in parsed if e["type"] == "patch"]
        assert len(patch_events) == 1

        p = patch_events[0]
        assert p["id"] == "SFR-001-01"
        assert p["field"] == "content"
        assert p["value"] == "새로운 내용"

    @pytest.mark.asyncio
    async def test_state_updated_after_patch(self):
        """PATCH 처리 후 state의 상세요구사항이 실제로 수정되어야 한다."""
        patch_json = json.dumps(
            {"id": "SFR-001-01", "field": "content", "value": "업데이트된 내용"}
        )
        mock_stream = _build_mock_stream([f"<PATCH>{patch_json}</PATCH>"])

        service = ChatService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            async for _ in service.chat_stream("test-session", "수정", [], _REQ_GROUP):
                pass

        details = state.get_detail()
        target = next(d for d in details if d.id == "SFR-001-01")
        assert target.content == "업데이트된 내용", "state의 content가 수정되어야 한다"
        assert target.is_modified is True, "is_modified가 True여야 한다"

    @pytest.mark.asyncio
    async def test_multiple_patches_all_applied(self):
        """여러 PATCH 태그가 있을 때 모두 적용되어야 한다."""
        patch1 = json.dumps({"id": "SFR-001-01", "field": "name", "value": "새 명칭1"})
        patch2 = json.dumps({"id": "SFR-001-02", "field": "content", "value": "새 내용2"})
        mock_stream = _build_mock_stream(
            [f"<PATCH>{patch1}</PATCH> <PATCH>{patch2}</PATCH>"]
        )

        service = ChatService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            events = []
            async for event in service.chat_stream("test-session", "수정", [], _REQ_GROUP):
                events.append(event)

        parsed = _parse_events(events)
        patch_events = [e for e in parsed if e["type"] == "patch"]
        assert len(patch_events) == 2, "patch 이벤트가 2건 발행되어야 한다"


# ---------------------------------------------------------------------------
# UT-004-03: 일반 질문 → text 이벤트만, patch 없음
# ---------------------------------------------------------------------------


class TestNoPatchForGeneralQuestion:
    """UT-004-03: PATCH 태그 없는 일반 질문은 text 이벤트만 발행해야 한다."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())
        state.set_detail(_make_details())

    @pytest.mark.asyncio
    async def test_no_patch_event_for_general_question(self):
        """PATCH 태그가 없는 응답에서는 patch 이벤트가 발행되지 않아야 한다."""
        mock_stream = _build_mock_stream(
            ["현재 요구사항은 총 2건입니다. 추가 질문이 있으신가요?"]
        )

        service = ChatService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            events = []
            async for event in service.chat_stream("test-session", "몇 건이에요?", [], _REQ_GROUP):
                events.append(event)

        parsed = _parse_events(events)
        patch_events = [e for e in parsed if e["type"] == "patch"]
        text_events = [e for e in parsed if e["type"] == "text"]

        assert len(patch_events) == 0, "일반 질문에는 patch 이벤트가 없어야 한다"
        assert len(text_events) >= 1, "text 이벤트가 1건 이상 있어야 한다"

    @pytest.mark.asyncio
    async def test_state_unchanged_for_general_question(self):
        """PATCH 태그 없는 응답은 state를 변경하지 않아야 한다."""
        mock_stream = _build_mock_stream(["현재 요구사항은 총 2건입니다."])

        service = ChatService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            async for _ in service.chat_stream("test-session", "몇 건이에요?", [], _REQ_GROUP):
                pass

        details = state.get_detail()
        modified_count = sum(1 for d in details if d.is_modified)
        assert modified_count == 0, "상태가 변경되지 않아야 한다"


# ---------------------------------------------------------------------------
# UT-004-04: Claude APIError → error 이벤트 발행
# ---------------------------------------------------------------------------


class TestChatStreamApiError:
    """UT-004-04: Claude APIError 발생 시 error 이벤트가 발행되어야 한다."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())
        state.set_detail(_make_details())

    @pytest.mark.asyncio
    async def test_api_error_yields_error_event(self):
        """Claude APIError 발생 시 type=error 이벤트가 발행되어야 한다."""
        from anthropic import APIError

        mock_request = MagicMock()
        api_error = APIError(message="연결 실패", request=mock_request, body=None)

        mock_stream = MagicMock()
        mock_stream.__aenter__ = AsyncMock(side_effect=api_error)
        mock_stream.__aexit__ = AsyncMock(return_value=False)

        service = ChatService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            events = []
            async for event in service.chat_stream("test-session", "수정해줘", [], _REQ_GROUP):
                events.append(event)

        assert len(events) == 1
        parsed = _parse_events(events)
        assert parsed[0]["type"] == "error"
        assert "message" in parsed[0]

    @pytest.mark.asyncio
    async def test_no_detail_yields_error_event(self):
        """상세요구사항이 없을 때 error 이벤트를 즉시 발행해야 한다."""
        state.reset_session()  # 상세요구사항 없는 상태

        service = ChatService()
        events = []
        async for event in service.chat_stream("test-session", "수정", [], _REQ_GROUP):
            events.append(event)

        assert len(events) == 1
        parsed = _parse_events(events)
        assert parsed[0]["type"] == "error"
