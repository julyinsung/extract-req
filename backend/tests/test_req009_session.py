"""REQ-009 claude_code_sdk 세션 기반 연속 실행 단위 테스트.

UT-009-01: AIGenerateServiceSDK.generate_stream() — 생성 완료 후 state.get_sdk_session_id()에 SDK session_id가 저장됨
UT-009-02: AIGenerateServiceSDK.generate_stream() — ResultMessage.session_id가 None이면 state 저장 없이 스트림 정상 완료
UT-009-03: ChatServiceSDK.chat_stream() — state.get_sdk_session_id()가 None이면 resume 없이 query() 호출됨
UT-009-04: ChatServiceSDK.chat_stream() — state.get_sdk_session_id()가 유효하면 ClaudeAgentOptions(resume=session_id)로 query() 호출됨
UT-009-05: state.reset_session() — 호출 후 state.get_sdk_session_id()가 None을 반환함
UT-009-06: state.set_sdk_session_id() / get_sdk_session_id() — 저장한 값이 조회 시 동일하게 반환됨
UT-009-07: SessionState — sdk_session_id 필드의 기본값이 None임
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

import app.state as state
from app.models.requirement import OriginalRequirement, DetailRequirement
from app.models.session import SessionState
from app.models.api import ChatMessage


# ---------------------------------------------------------------------------
# 픽스처 헬퍼
# ---------------------------------------------------------------------------


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
    ]


def _make_sdk_assistant_message(text: str):
    """claude_agent_sdk AssistantMessage mock을 생성한다."""
    from claude_agent_sdk import AssistantMessage, TextBlock

    block = TextBlock(text=text)
    msg = MagicMock(spec=AssistantMessage)
    msg.__class__ = AssistantMessage
    msg.content = [block]
    return msg


def _make_sdk_result_message(result: str = "", session_id: str | None = None):
    """claude_agent_sdk ResultMessage mock을 생성한다.

    Args:
        result: 최종 응답 텍스트
        session_id: SDK가 반환하는 세션 식별자 (None이면 속성 없음으로 처리)
    """
    from claude_agent_sdk import ResultMessage

    msg = MagicMock(spec=ResultMessage)
    msg.__class__ = ResultMessage
    msg.result = result
    msg.session_id = session_id
    return msg


def _make_sdk_stream(messages: list):
    """query()가 반환하는 async iterator mock을 생성한다."""
    async def _stream():
        for msg in messages:
            yield msg

    return _stream()


def _parse_events(events: list[str]) -> list[dict]:
    """SSE 이벤트 문자열 목록을 dict 목록으로 파싱한다."""
    result = []
    for e in events:
        raw = e.removeprefix("data: ").strip()
        if raw:
            result.append(json.loads(raw))
    return result


# ---------------------------------------------------------------------------
# UT-009-07: SessionState 기본값 확인 (의존성 없음 — 가장 먼저 실행)
# ---------------------------------------------------------------------------


class TestSessionStateDefault:
    """UT-009-07: SessionState.sdk_session_id 필드 기본값 확인."""

    def test_ut_009_07_sdk_session_id_default_is_none(self):
        """UT-009-07: 새로 생성된 SessionState의 sdk_session_id 기본값이 None이어야 한다."""
        session = SessionState()
        assert session.sdk_session_id is None, (
            "SessionState.sdk_session_id의 기본값이 None이어야 한다"
        )


# ---------------------------------------------------------------------------
# UT-009-05, UT-009-06: state 함수 단위 테스트
# ---------------------------------------------------------------------------


class TestStateSDKSessionFunctions:
    """UT-009-05, UT-009-06: get/set_sdk_session_id, reset_session 테스트."""

    def setup_method(self):
        """각 테스트 전 세션 초기화."""
        state.reset_session()

    def test_ut_009_06_set_and_get_sdk_session_id_returns_same_value(self):
        """UT-009-06: set_sdk_session_id로 저장한 값이 get_sdk_session_id에서 동일하게 반환된다."""
        expected = "sess-test-abc123"
        state.set_sdk_session_id(expected)
        actual = state.get_sdk_session_id()
        assert actual == expected, (
            f"저장한 session_id({expected})와 조회된 값({actual})이 일치해야 한다"
        )

    def test_ut_009_05_reset_session_clears_sdk_session_id(self):
        """UT-009-05: reset_session() 호출 후 get_sdk_session_id()가 None을 반환한다."""
        state.set_sdk_session_id("sess-xyz789")
        assert state.get_sdk_session_id() == "sess-xyz789"  # 사전 조건 확인

        state.reset_session()

        assert state.get_sdk_session_id() is None, (
            "reset_session() 후 sdk_session_id가 None이어야 한다"
        )

    def test_get_sdk_session_id_initial_state_is_none(self):
        """초기 상태(reset 직후)에서 get_sdk_session_id()가 None을 반환한다."""
        assert state.get_sdk_session_id() is None


# ---------------------------------------------------------------------------
# UT-009-01, UT-009-02: AIGenerateServiceSDK session_id 저장 테스트
# ---------------------------------------------------------------------------


class TestAIGenerateServiceSDKSessionId:
    """UT-009-01, UT-009-02: generate_stream()에서 ResultMessage session_id 저장 테스트."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())

    @pytest.mark.asyncio
    async def test_ut_009_01_generate_stream_saves_session_id_on_completion(self):
        """UT-009-01: 생성 완료 후 state.get_sdk_session_id()에 SDK session_id가 저장된다."""
        from app.services.ai_generate_service_sdk import AIGenerateServiceSDK

        expected_session_id = "sess-generated-111"
        item_json = json.dumps({
            "id": "SFR-001-01",
            "parent_id": "SFR-001",
            "category": "기능",
            "name": "UI",
            "content": "업로드 기능",
        }, ensure_ascii=False)

        sdk_messages = [
            _make_sdk_assistant_message(f"[{item_json}]"),
            _make_sdk_result_message("", session_id=expected_session_id),
        ]

        service = AIGenerateServiceSDK()
        with patch("app.services.ai_generate_service_sdk.query", return_value=_make_sdk_stream(sdk_messages)):
            events = []
            async for event in service.generate_stream("test-session"):
                events.append(event)

        parsed = _parse_events(events)
        # 스트림이 done 이벤트로 정상 완료되어야 한다
        assert any(e["type"] == "done" for e in parsed), "done 이벤트가 발행되어야 한다"

        # session_id가 state에 저장되어야 한다
        actual = state.get_sdk_session_id()
        assert actual == expected_session_id, (
            f"state에 저장된 session_id({actual})가 "
            f"ResultMessage의 session_id({expected_session_id})와 일치해야 한다"
        )

    @pytest.mark.asyncio
    async def test_ut_009_02_generate_stream_skips_save_when_session_id_is_none(self):
        """UT-009-02: ResultMessage.session_id가 None이면 state 저장 없이 스트림이 정상 완료된다."""
        from app.services.ai_generate_service_sdk import AIGenerateServiceSDK

        item_json = json.dumps({
            "id": "SFR-001-01",
            "parent_id": "SFR-001",
            "category": "기능",
            "name": "UI",
            "content": "업로드 기능",
        }, ensure_ascii=False)

        sdk_messages = [
            _make_sdk_assistant_message(f"[{item_json}]"),
            _make_sdk_result_message("", session_id=None),
        ]

        service = AIGenerateServiceSDK()
        with patch("app.services.ai_generate_service_sdk.query", return_value=_make_sdk_stream(sdk_messages)):
            events = []
            async for event in service.generate_stream("test-session"):
                events.append(event)

        parsed = _parse_events(events)
        # 스트림이 done 이벤트로 정상 완료되어야 한다 (예외 없음)
        assert any(e["type"] == "done" for e in parsed), "done 이벤트가 발행되어야 한다"

        # session_id가 None인 경우 state에 저장되지 않아야 한다
        assert state.get_sdk_session_id() is None, (
            "ResultMessage.session_id=None이면 state.sdk_session_id가 None으로 유지되어야 한다"
        )


# ---------------------------------------------------------------------------
# UT-009-03, UT-009-04: ChatServiceSDK resume 파라미터 테스트
# ---------------------------------------------------------------------------


class TestChatServiceSDKResume:
    """UT-009-03, UT-009-04: chat_stream()의 ClaudeAgentOptions resume 파라미터 테스트."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())
        state.set_detail(_make_details())

    @pytest.mark.asyncio
    async def test_ut_009_03_chat_stream_calls_query_without_resume_when_no_session_id(self):
        """UT-009-03: state.get_sdk_session_id()가 None이면 resume 없이 query()가 호출된다."""
        from app.services.chat_service_sdk import ChatServiceSDK
        from claude_agent_sdk import ClaudeAgentOptions

        # sdk_session_id가 None인 상태 (setup_method에서 reset_session 호출됨)
        assert state.get_sdk_session_id() is None

        captured_options: list[ClaudeAgentOptions] = []

        async def _mock_stream():
            yield _make_sdk_assistant_message("응답입니다.")
            yield _make_sdk_result_message("")

        def _mock_query(prompt, options):
            captured_options.append(options)
            return _mock_stream()

        service = ChatServiceSDK()
        with patch("app.services.chat_service_sdk.query", side_effect=_mock_query):
            events = []
            async for event in service.chat_stream("test-session", "수정해줘", []):
                events.append(event)

        assert len(captured_options) == 1, "query()가 정확히 1회 호출되어야 한다"
        options = captured_options[0]
        # resume 파라미터가 없거나 None이어야 한다
        resume_val = getattr(options, "resume", None)
        assert resume_val is None, (
            f"sdk_session_id가 None이면 ClaudeAgentOptions에 resume이 없어야 한다. "
            f"실제값: {resume_val}"
        )

    @pytest.mark.asyncio
    async def test_ut_009_04_chat_stream_calls_query_with_resume_when_session_id_exists(self):
        """UT-009-04: state.get_sdk_session_id()가 유효한 값이면 ClaudeAgentOptions(resume=session_id)로 query()가 호출된다."""
        from app.services.chat_service_sdk import ChatServiceSDK
        from claude_agent_sdk import ClaudeAgentOptions

        stored_session_id = "sess-abc123"
        state.set_sdk_session_id(stored_session_id)
        assert state.get_sdk_session_id() == stored_session_id  # 사전 조건 확인

        captured_options: list[ClaudeAgentOptions] = []

        async def _mock_stream():
            yield _make_sdk_assistant_message("응답입니다.")
            yield _make_sdk_result_message("")

        def _mock_query(prompt, options):
            captured_options.append(options)
            return _mock_stream()

        service = ChatServiceSDK()
        with patch("app.services.chat_service_sdk.query", side_effect=_mock_query):
            events = []
            async for event in service.chat_stream("test-session", "수정해줘", []):
                events.append(event)

        assert len(captured_options) == 1, "query()가 정확히 1회 호출되어야 한다"
        options = captured_options[0]
        resume_val = getattr(options, "resume", None)
        assert resume_val == stored_session_id, (
            f"ClaudeAgentOptions의 resume이 저장된 session_id({stored_session_id})여야 한다. "
            f"실제값: {resume_val}"
        )
