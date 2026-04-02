"""REQ-004/009/010 신규 기능 단위 테스트.

UT-004-06: state.get_original_by_group() — req_group에 해당하는 원본 요구사항 1건 반환
UT-004-07: state.get_detail_by_group() — parent_id == req_group인 상세항목만 반환, 다른 그룹 미포함
UT-004-08: state.replace_detail_group() — 해당 그룹 기존 상세항목 전체 교체, is_modified = True
UT-004-09: state.replace_detail_group() — 다른 그룹 상세항목은 변경되지 않음
UT-004-11: ChatService.chat_stream() — <REPLACE> 태그 감지 시 replace SSE 이벤트 발행
UT-004-12: ChatService.chat_stream() — <REPLACE> 태그 내부 JSON 파싱 실패 시 replace 이벤트 없이 done 발행
UT-009-05: SessionState.sdk_sessions — 기본값이 빈 딕셔너리 {}
UT-009-06: state.set/get_sdk_session_id(req_group) — 저장한 값이 조회 시 동일하게 반환
UT-009-07: state.get_sdk_session_id(req_group) — 저장되지 않은 그룹 조회 시 None 반환
UT-009-08: state.set_sdk_session_id(A, B 독립) — A에 저장해도 B에 영향 없음
UT-009-09: state.reset_session() — 호출 후 sdk_sessions가 {} 로 초기화
UT-010-01: AiGenerateService.generate_stream() — item 이벤트 직후 progress 이벤트 발행 확인
UT-010-03: AiGenerateService.generate_stream() — progress.current가 parent_id 완료 순서(1-based)와 일치
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import app.state as state
from app.models.requirement import DetailRequirement, OriginalRequirement
from app.models.session import SessionState


# ---------------------------------------------------------------------------
# 픽스처 헬퍼
# ---------------------------------------------------------------------------


def _make_originals_two_groups() -> list[OriginalRequirement]:
    """테스트용 원본 요구사항 픽스처 (2개 그룹)."""
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


def _make_details_two_groups() -> list[DetailRequirement]:
    """테스트용 상세요구사항 픽스처 (2개 그룹)."""
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
        DetailRequirement(
            id="SFR-002-01",
            parent_id="SFR-002",
            category="기능요구사항",
            name="엑셀 다운로드",
            content="결과를 xlsx 파일로 내보낸다.",
            order_index=0,
        ),
    ]


def _parse_events(events: list[str]) -> list[dict]:
    """SSE 이벤트 문자열 목록을 dict 목록으로 파싱한다."""
    result = []
    for e in events:
        raw = e.removeprefix("data: ").strip()
        if raw:
            result.append(json.loads(raw))
    return result


# ---------------------------------------------------------------------------
# UT-004-06, UT-004-07: state 필터링 함수 테스트
# ---------------------------------------------------------------------------


class TestStateGroupFunctions:
    """UT-004-06, UT-004-07: get_original_by_group / get_detail_by_group 테스트."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals_two_groups())
        state.set_detail(_make_details_two_groups())

    def test_ut_004_06_get_original_by_group_returns_matching_item(self):
        """UT-004-06: req_group에 해당하는 원본 요구사항 1건을 반환한다."""
        result = state.get_original_by_group("SFR-001")
        assert result is not None, "SFR-001 원본 요구사항이 반환되어야 한다"
        assert result.id == "SFR-001"
        assert result.name == "파일 업로드"

    def test_ut_004_06_get_original_by_group_returns_none_for_unknown(self):
        """UT-004-06: 존재하지 않는 req_group 조회 시 None을 반환한다."""
        result = state.get_original_by_group("SFR-999")
        assert result is None, "존재하지 않는 그룹은 None을 반환해야 한다"

    def test_ut_004_07_get_detail_by_group_returns_only_matching_group(self):
        """UT-004-07: parent_id == req_group인 상세항목만 반환하고 다른 그룹 항목을 포함하지 않는다."""
        result = state.get_detail_by_group("SFR-001")
        assert len(result) == 2, "SFR-001 상세항목이 2건 반환되어야 한다"
        for item in result:
            assert item.parent_id == "SFR-001", "반환된 항목의 parent_id가 SFR-001이어야 한다"

    def test_ut_004_07_get_detail_by_group_excludes_other_groups(self):
        """UT-004-07: 다른 그룹의 상세항목은 반환하지 않는다."""
        result = state.get_detail_by_group("SFR-001")
        ids = [r.id for r in result]
        assert "SFR-002-01" not in ids, "SFR-002-01이 SFR-001 결과에 포함되지 않아야 한다"

    def test_ut_004_07_get_detail_by_group_returns_empty_for_unknown(self):
        """UT-004-07: 상세항목이 없는 그룹 조회 시 빈 목록을 반환한다."""
        result = state.get_detail_by_group("SFR-999")
        assert result == [], "존재하지 않는 그룹의 상세항목은 빈 목록이어야 한다"


# ---------------------------------------------------------------------------
# UT-004-08, UT-004-09: state.replace_detail_group 테스트
# ---------------------------------------------------------------------------


class TestReplaceDetailGroup:
    """UT-004-08, UT-004-09: replace_detail_group 테스트."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals_two_groups())
        state.set_detail(_make_details_two_groups())

    def test_ut_004_08_replace_replaces_all_items_in_group(self):
        """UT-004-08: 해당 그룹의 기존 상세항목이 전체 교체되고 is_modified가 True로 설정된다."""
        new_items = [
            DetailRequirement(
                id="SFR-001-01",
                parent_id="SFR-001",
                category="기능요구사항",
                name="새로운 업로드",
                content="새로운 내용",
                order_index=0,
            )
        ]
        state.replace_detail_group("SFR-001", new_items)

        result = state.get_detail_by_group("SFR-001")
        assert len(result) == 1, "교체 후 SFR-001 상세항목이 1건이어야 한다"
        assert result[0].name == "새로운 업로드"
        assert result[0].is_modified is True, "교체된 항목의 is_modified가 True여야 한다"

    def test_ut_004_09_replace_does_not_affect_other_groups(self):
        """UT-004-09: 다른 그룹의 상세항목은 변경되지 않는다."""
        new_items = [
            DetailRequirement(
                id="SFR-001-01",
                parent_id="SFR-001",
                category="기능요구사항",
                name="교체된 항목",
                content="교체된 내용",
                order_index=0,
            )
        ]
        state.replace_detail_group("SFR-001", new_items)

        sfr002_items = state.get_detail_by_group("SFR-002")
        assert len(sfr002_items) == 1, "SFR-002 상세항목이 변경되지 않아야 한다"
        assert sfr002_items[0].id == "SFR-002-01"
        assert sfr002_items[0].name == "엑셀 다운로드"


# ---------------------------------------------------------------------------
# UT-004-11, UT-004-12: ChatService REPLACE 태그 처리 테스트 (anthropic 독립)
# ---------------------------------------------------------------------------


class TestProcessReplace:
    """UT-004-11, UT-004-12: _process_replace 함수 직접 테스트."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals_two_groups())
        state.set_detail(_make_details_two_groups())

    def test_ut_004_11_process_replace_emits_replace_event(self):
        """UT-004-11: REPLACE 태그 감지 시 replace SSE 이벤트를 발행하고 state를 교체한다."""
        from app.services.chat_service import _process_replace

        replace_content = json.dumps([
            {"name": "새 항목1", "content": "새 내용1", "category": "기능요구사항"},
            {"name": "새 항목2", "content": "새 내용2", "category": "기능요구사항"},
        ], ensure_ascii=False)
        full_text = f"설명 텍스트입니다. <REPLACE>{replace_content}</REPLACE>"

        events = list(_process_replace(full_text, "SFR-001"))

        assert len(events) == 1, "REPLACE 태그 1건당 replace 이벤트 1건이 발행되어야 한다"
        parsed = json.loads(events[0].removeprefix("data: ").strip())
        assert parsed["type"] == "replace"
        assert parsed["req_group"] == "SFR-001"
        assert len(parsed["items"]) == 2

        # state도 교체되었는지 확인
        sfr001_items = state.get_detail_by_group("SFR-001")
        assert len(sfr001_items) == 2
        names = [item.name for item in sfr001_items]
        assert "새 항목1" in names

    def test_ut_004_11_replace_items_have_correct_ids(self):
        """UT-004-11: 교체된 항목의 id가 {req_group}-{NN} 형식이어야 한다."""
        from app.services.chat_service import _process_replace

        replace_content = json.dumps([
            {"name": "항목A", "content": "내용A", "category": "기능"},
        ], ensure_ascii=False)
        full_text = f"<REPLACE>{replace_content}</REPLACE>"

        events = list(_process_replace(full_text, "SFR-001"))

        parsed = json.loads(events[0].removeprefix("data: ").strip())
        item = parsed["items"][0]
        assert item["id"] == "SFR-001-01", f"id가 SFR-001-01이어야 한다. 실제: {item['id']}"
        assert item["is_modified"] is True

    def test_ut_004_12_replace_invalid_json_skips_silently(self):
        """UT-004-12: REPLACE 태그 내부 JSON 파싱 실패 시 이벤트 없이 완료된다."""
        from app.services.chat_service import _process_replace

        full_text = "<REPLACE>not valid json[[[</REPLACE>"

        events = list(_process_replace(full_text, "SFR-001"))

        assert len(events) == 0, "JSON 파싱 실패 시 이벤트가 발행되지 않아야 한다"

        # state는 변경되지 않아야 한다
        sfr001_items = state.get_detail_by_group("SFR-001")
        assert len(sfr001_items) == 2, "state가 변경되지 않아야 한다"

    def test_ut_004_12_replace_non_list_json_skips_silently(self):
        """UT-004-12: REPLACE 태그 내부가 배열이 아닌 경우 이벤트 없이 완료된다."""
        from app.services.chat_service import _process_replace

        full_text = '<REPLACE>{"not": "a list"}</REPLACE>'

        events = list(_process_replace(full_text, "SFR-001"))

        assert len(events) == 0, "배열이 아닌 경우 이벤트가 발행되지 않아야 한다"


# ---------------------------------------------------------------------------
# UT-009-05~09: state SDK 세션 그룹별 관리 (이미 test_req009_session.py에 있으나 여기서도 검증)
# ---------------------------------------------------------------------------


class TestSDKSessionGroupManagement:
    """UT-009-05~09: 그룹별 SDK session_id 관리 핵심 케이스."""

    def setup_method(self):
        state.reset_session()

    def test_ut_009_05_sdk_sessions_default_is_empty_dict(self):
        """UT-009-05: 새 SessionState의 sdk_sessions 기본값이 빈 딕셔너리이다."""
        session = SessionState()
        assert session.sdk_sessions == {}

    def test_ut_009_06_set_and_get_returns_same_value(self):
        """UT-009-06: set_sdk_session_id(req_group, sid)로 저장한 값이 get에서 동일하게 반환된다."""
        state.set_sdk_session_id("REQ-001", "sess-aaa")
        assert state.get_sdk_session_id("REQ-001") == "sess-aaa"

    def test_ut_009_07_get_returns_none_for_unset_group(self):
        """UT-009-07: 저장되지 않은 그룹 키 조회 시 None을 반환한다."""
        assert state.get_sdk_session_id("REQ-999") is None

    def test_ut_009_08_groups_are_independent(self):
        """UT-009-08: 그룹 A에 저장해도 그룹 B의 session_id에 영향을 주지 않는다."""
        state.set_sdk_session_id("REQ-001", "sess-a")
        state.set_sdk_session_id("REQ-002", "sess-b")

        state.set_sdk_session_id("REQ-001", "sess-a-new")

        assert state.get_sdk_session_id("REQ-002") == "sess-b"

    def test_ut_009_09_reset_session_clears_all_sessions(self):
        """UT-009-09: reset_session() 후 sdk_sessions가 빈 딕셔너리로 초기화된다."""
        state.set_sdk_session_id("REQ-001", "sess-a")
        state.set_sdk_session_id("REQ-002", "sess-b")

        state.reset_session()

        session = state.get_session()
        assert session.sdk_sessions == {}


# ---------------------------------------------------------------------------
# UT-010-01, UT-010-03: AiGenerateService progress 이벤트 테스트
# ---------------------------------------------------------------------------


class TestGenerateServiceProgress:
    """UT-010-01, UT-010-03: AiGenerateService.generate_stream() progress 이벤트 테스트."""

    def setup_method(self):
        state.reset_session()
        state.set_original([
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
        ])

    @pytest.mark.asyncio
    async def test_ut_010_01_progress_event_emitted_after_group_completes(self):
        """UT-010-01: item 이벤트 직후 progress 이벤트가 발행되어야 한다 (current=1, total=N)."""
        # anthropic 패키지 없는 환경에서는 AiGenerateService 인스턴스화가 불가 — 스킵
        anthropic = pytest.importorskip("anthropic", reason="anthropic 모듈 없음")
        from app.services.ai_generate_service import AiGenerateService

        chunks = [
            '[{"id":"SFR-001-01","parent_id":"SFR-001","category":"기능","name":"UI","content":"업로드"},'
            '{"id":"SFR-002-01","parent_id":"SFR-002","category":"기능","name":"다운로드","content":"내보내기"}]'
        ]

        async def _text_stream():
            for chunk in chunks:
                yield chunk

        mock_stream = MagicMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock(return_value=False)
        mock_stream.text_stream = _text_stream()

        service = AiGenerateService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            events = []
            async for event in service.generate_stream("test-session"):
                events.append(event)

        parsed = _parse_events(events)
        progress_events = [e for e in parsed if e["type"] == "progress"]
        assert len(progress_events) >= 1, "progress 이벤트가 1건 이상 발행되어야 한다"

        first_progress = progress_events[0]
        assert "current" in first_progress
        assert "total" in first_progress
        assert "req_id" in first_progress
        assert first_progress["current"] >= 1
        assert first_progress["total"] == 2

    @pytest.mark.asyncio
    async def test_ut_010_03_progress_current_matches_completion_order(self):
        """UT-010-03: progress.current가 parent_id 완료 순서(1-based)와 일치한다."""
        # anthropic 패키지 없는 환경에서는 AiGenerateService 인스턴스화가 불가 — 스킵
        pytest.importorskip("anthropic", reason="anthropic 모듈 없음")
        from app.services.ai_generate_service import AiGenerateService

        chunks = [
            '[{"id":"SFR-001-01","parent_id":"SFR-001","category":"기능","name":"UI","content":"업로드"},'
            '{"id":"SFR-002-01","parent_id":"SFR-002","category":"기능","name":"다운로드","content":"내보내기"}]'
        ]

        async def _text_stream():
            for chunk in chunks:
                yield chunk

        mock_stream = MagicMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock(return_value=False)
        mock_stream.text_stream = _text_stream()

        service = AiGenerateService()
        with patch.object(service.client.messages, "stream", return_value=mock_stream):
            events = []
            async for event in service.generate_stream("test-session"):
                events.append(event)

        parsed = _parse_events(events)
        progress_events = [e for e in parsed if e["type"] == "progress"]

        # current 값이 1-based 순서여야 한다
        currents = [e["current"] for e in progress_events]
        for i, current in enumerate(currents):
            assert current == i + 1, (
                f"progress.current가 {i + 1}이어야 한다. 실제: {current}"
            )
