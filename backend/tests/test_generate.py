"""AI 상세요구사항 생성 서비스 단위 테스트.

UT-002-01: 정상 세션 → item 이벤트 1건 이상 발행
UT-002-02: Claude APIError → error 이벤트 발행
UT-002-03: 1:N 구조 — 각 parent_id에 1개 이상 DetailRequirement 생성
UT-002-04: ID 채번 — {parent_id}-{NN} 형식 준수, 중복 없음

실제 Claude API 호출 없이 AsyncMock으로 스트리밍 응답을 모의한다.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import app.state as state
from app.models.requirement import OriginalRequirement
from app.services.ai_generate_service import AiGenerateService, _find_obj_end, _sse


# ---------------------------------------------------------------------------
# 픽스처
# ---------------------------------------------------------------------------


def _make_originals() -> list[OriginalRequirement]:
    """테스트용 원본 요구사항 픽스처 — parent가 2개인 1:N 구조."""
    return [
        OriginalRequirement(
            id="SFR-001",
            category="기능요구사항",
            name="파일 업로드",
            content="사용자는 HWP 파일을 업로드할 수 있다.",
            order_index=0,
        ),
        OriginalRequirement(
            id="SFR-002",
            category="기능요구사항",
            name="결과 다운로드",
            content="사용자는 결과를 엑셀로 다운로드할 수 있다.",
            order_index=1,
        ),
    ]


def _make_stream_chunks(items: list[dict]) -> list[str]:
    """JSON 객체 목록을 청크로 나누어 스트리밍 상황을 시뮬레이션한다.

    실제 API는 임의의 위치에서 청크를 잘라 전달하므로,
    각 객체를 두 조각으로 분리하여 버퍼 누적 로직을 검증한다.
    """
    chunks = ["["]
    for i, item in enumerate(items):
        s = json.dumps(item, ensure_ascii=False)
        mid = len(s) // 2
        chunks.append(s[:mid])
        chunks.append(s[mid:])
        if i < len(items) - 1:
            chunks.append(",")
    chunks.append("]")
    return chunks


def _build_mock_stream(chunks: list[str]):
    """text_stream async generator를 흉내 내는 mock 컨텍스트 매니저를 반환한다."""

    async def _text_stream():
        for chunk in chunks:
            yield chunk

    mock_stream = MagicMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=False)
    mock_stream.text_stream = _text_stream()
    return mock_stream


# ---------------------------------------------------------------------------
# UT-002-01: 정상 세션 → item 이벤트 1건 이상 발행
# ---------------------------------------------------------------------------


class TestGenerateStreamNormal:
    """UT-002-01: 정상 세션에서 item 이벤트가 1건 이상 발행되어야 한다."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())

    @pytest.mark.asyncio
    async def test_item_events_emitted(self):
        """정상 스트리밍 응답 시 item 이벤트가 1건 이상 발행되어야 한다."""
        items = [
            {"id": "SFR-001-01", "parent_id": "SFR-001", "category": "기능", "name": "UI", "content": "드래그앤드롭"},
            {"id": "SFR-001-02", "parent_id": "SFR-001", "category": "기능", "name": "검증", "content": "파일 유효성"},
        ]
        mock_stream = _build_mock_stream(_make_stream_chunks(items))

        service = AiGenerateService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            events = []
            async for event in service.generate_stream("test-session"):
                events.append(event)

        item_events = [e for e in events if '"type": "item"' in e]
        assert len(item_events) >= 1, "item 이벤트가 1건 이상 발행되어야 한다"

    @pytest.mark.asyncio
    async def test_done_event_emitted_at_end(self):
        """스트리밍 완료 후 done 이벤트가 마지막으로 발행되어야 한다."""
        items = [
            {"id": "SFR-001-01", "parent_id": "SFR-001", "category": "기능", "name": "UI", "content": "내용"},
        ]
        mock_stream = _build_mock_stream(_make_stream_chunks(items))

        service = AiGenerateService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            events = []
            async for event in service.generate_stream("test-session"):
                events.append(event)

        assert events, "이벤트가 최소 1건은 있어야 한다"
        last_event = events[-1]
        parsed = json.loads(last_event.removeprefix("data: ").strip())
        assert parsed["type"] == "done"
        assert "total" in parsed


# ---------------------------------------------------------------------------
# UT-002-02: Claude APIError → error 이벤트 발행
# ---------------------------------------------------------------------------


class TestGenerateStreamApiError:
    """UT-002-02: Claude APIError 발생 시 error 이벤트가 발행되어야 한다."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())

    @pytest.mark.asyncio
    async def test_api_error_yields_error_event(self):
        """Claude APIError 발생 시 type=error 이벤트가 발행되어야 한다."""
        from anthropic import APIError

        # APIError는 request 인자를 요구한다 — MagicMock으로 대체한다
        mock_request = MagicMock()
        api_error = APIError(message="연결 실패", request=mock_request, body=None)

        mock_stream = MagicMock()
        mock_stream.__aenter__ = AsyncMock(side_effect=api_error)
        mock_stream.__aexit__ = AsyncMock(return_value=False)

        service = AiGenerateService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            events = []
            async for event in service.generate_stream("test-session"):
                events.append(event)

        assert len(events) == 1
        parsed = json.loads(events[0].removeprefix("data: ").strip())
        assert parsed["type"] == "error"
        assert "message" in parsed

    @pytest.mark.asyncio
    async def test_empty_originals_yields_error_event(self):
        """원본 요구사항이 없으면 error 이벤트를 즉시 발행해야 한다."""
        state.reset_session()  # 원본 없는 상태

        service = AiGenerateService()
        events = []
        async for event in service.generate_stream("test-session"):
            events.append(event)

        assert len(events) == 1
        parsed = json.loads(events[0].removeprefix("data: ").strip())
        assert parsed["type"] == "error"


# ---------------------------------------------------------------------------
# UT-002-03: 1:N 구조 — 각 parent_id에 1개 이상 DetailRequirement 생성
# ---------------------------------------------------------------------------


class TestOneToManyStructure:
    """UT-002-03: 각 parent_id에 대해 DetailRequirement가 1개 이상 생성되어야 한다."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())

    @pytest.mark.asyncio
    async def test_each_parent_has_at_least_one_detail(self):
        """2개의 parent_id 각각에 대해 1개 이상의 DetailRequirement가 생성되어야 한다."""
        items = [
            {"id": "SFR-001-01", "parent_id": "SFR-001", "category": "기능", "name": "UI", "content": "내용1"},
            {"id": "SFR-001-02", "parent_id": "SFR-001", "category": "기능", "name": "검증", "content": "내용2"},
            {"id": "SFR-002-01", "parent_id": "SFR-002", "category": "기능", "name": "다운로드", "content": "내용3"},
        ]
        mock_stream = _build_mock_stream(_make_stream_chunks(items))

        service = AiGenerateService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            async for _ in service.generate_stream("test-session"):
                pass

        details = state.get_detail()
        parent_ids = {d.parent_id for d in details}
        assert "SFR-001" in parent_ids, "SFR-001의 상세요구사항이 있어야 한다"
        assert "SFR-002" in parent_ids, "SFR-002의 상세요구사항이 있어야 한다"

        for pid in parent_ids:
            count = sum(1 for d in details if d.parent_id == pid)
            assert count >= 1, f"{pid}에 DetailRequirement가 1개 이상이어야 한다"

    @pytest.mark.asyncio
    async def test_details_stored_in_state(self):
        """스트리밍 완료 후 state에 DetailRequirement가 저장되어야 한다."""
        items = [
            {"id": "SFR-001-01", "parent_id": "SFR-001", "category": "기능", "name": "UI", "content": "내용"},
        ]
        mock_stream = _build_mock_stream(_make_stream_chunks(items))

        service = AiGenerateService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            async for _ in service.generate_stream("test-session"):
                pass

        assert len(state.get_detail()) >= 1


# ---------------------------------------------------------------------------
# UT-002-04: ID 채번 — {parent_id}-{NN} 형식 준수, 중복 없음
# ---------------------------------------------------------------------------


class TestIdNaming:
    """UT-002-04: 생성된 DetailRequirement의 ID가 {parent_id}-{NN} 형식이고 중복이 없어야 한다."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())

    @pytest.mark.asyncio
    async def test_ids_follow_naming_convention(self):
        """생성된 ID가 {parent_id}-{NN} 형식을 준수해야 한다."""
        items = [
            {"id": "SFR-001-01", "parent_id": "SFR-001", "category": "기능", "name": "UI", "content": "내용1"},
            {"id": "SFR-001-02", "parent_id": "SFR-001", "category": "기능", "name": "검증", "content": "내용2"},
            {"id": "SFR-002-01", "parent_id": "SFR-002", "category": "기능", "name": "다운로드", "content": "내용3"},
        ]
        mock_stream = _build_mock_stream(_make_stream_chunks(items))

        service = AiGenerateService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            async for _ in service.generate_stream("test-session"):
                pass

        details = state.get_detail()
        for detail in details:
            # {parent_id}-{NN} 형식: id가 parent_id로 시작하고 '-NN' 접미사를 가져야 한다
            assert detail.id.startswith(detail.parent_id), (
                f"id '{detail.id}'가 parent_id '{detail.parent_id}'로 시작해야 한다"
            )
            suffix = detail.id[len(detail.parent_id):]
            assert suffix.startswith("-"), f"id '{detail.id}'에 '-NN' 접미사가 있어야 한다"
            seq_part = suffix[1:]
            assert seq_part.isdigit() and len(seq_part) == 2, (
                f"id '{detail.id}'의 시퀀스 '{seq_part}'가 두 자리 숫자여야 한다"
            )

    @pytest.mark.asyncio
    async def test_ids_are_unique(self):
        """생성된 DetailRequirement의 ID에 중복이 없어야 한다."""
        items = [
            {"id": "SFR-001-01", "parent_id": "SFR-001", "category": "기능", "name": "A", "content": "내용A"},
            {"id": "SFR-001-02", "parent_id": "SFR-001", "category": "기능", "name": "B", "content": "내용B"},
            {"id": "SFR-002-01", "parent_id": "SFR-002", "category": "기능", "name": "C", "content": "내용C"},
            {"id": "SFR-002-02", "parent_id": "SFR-002", "category": "기능", "name": "D", "content": "내용D"},
        ]
        mock_stream = _build_mock_stream(_make_stream_chunks(items))

        service = AiGenerateService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            async for _ in service.generate_stream("test-session"):
                pass

        details = state.get_detail()
        ids = [d.id for d in details]
        assert len(ids) == len(set(ids)), "ID에 중복이 없어야 한다"

    @pytest.mark.asyncio
    async def test_server_corrects_missing_id(self):
        """AI 응답에 id가 없으면 서버에서 parent_id + 시퀀스로 채번해야 한다."""
        # id 필드를 의도적으로 누락한 객체
        items = [
            {"parent_id": "SFR-001", "category": "기능", "name": "UI", "content": "내용"},
        ]
        mock_stream = _build_mock_stream(_make_stream_chunks(items))

        service = AiGenerateService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            async for _ in service.generate_stream("test-session"):
                pass

        details = state.get_detail()
        assert len(details) == 1
        assert details[0].id == "SFR-001-01", (
            f"서버 채번 ID가 'SFR-001-01'이어야 하지만 '{details[0].id}'가 반환됐다"
        )


# ---------------------------------------------------------------------------
# 보조 함수 단위 테스트
# ---------------------------------------------------------------------------


class TestFindObjEnd:
    """_find_obj_end 헬퍼 함수 검증."""

    def test_simple_object(self):
        s = '{"key": "value"}'
        assert _find_obj_end(s, 0) == len(s) - 1

    def test_nested_object(self):
        s = '{"a": {"b": 1}}'
        assert _find_obj_end(s, 0) == len(s) - 1

    def test_incomplete_object(self):
        s = '{"key": "val'
        assert _find_obj_end(s, 0) == -1

    def test_brace_in_string(self):
        """문자열 내 중괄호는 depth 계산에서 제외되어야 한다."""
        s = '{"key": "va{lue}"}'
        assert _find_obj_end(s, 0) == len(s) - 1
