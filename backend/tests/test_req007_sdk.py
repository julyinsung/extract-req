"""REQ-007 AI 백엔드 선택 옵션 단위 테스트.

UT-007-01: AI_BACKEND=anthropic_api → AiGenerateService 인스턴스 반환
UT-007-02: AI_BACKEND=claude_code_sdk → AIGenerateServiceSDK 인스턴스 반환
UT-007-03: AI_BACKEND 미설정(기본값) → AIGenerateServiceSDK 인스턴스 반환
UT-007-04: AI_BACKEND=invalid_value → AIGenerateServiceSDK 폴백 반환 (앱 크래시 없음)
UT-007-05: AI_BACKEND=anthropic_api → ChatService 인스턴스 반환
UT-007-06: AI_BACKEND=claude_code_sdk → ChatServiceSDK 인스턴스 반환
UT-007-07: AIGenerateServiceSDK.generate_stream() — SDK 정상 응답 → item 이벤트 1건 이상 발행
UT-007-08: AIGenerateServiceSDK.generate_stream() — SSE item 이벤트 구조가 AiGenerateService와 동일
UT-007-09: AIGenerateServiceSDK.generate_stream() — SDK 예외 발생 → error SSE 이벤트 발행 (앱 크래시 없음)
UT-007-10: AIGenerateServiceSDK.generate_stream() — 원본 요구사항 없을 때 → error SSE 이벤트 발행
UT-007-11: ChatServiceSDK.chat_stream() — SDK 정상 응답 → text 이벤트 발행
UT-007-12: ChatServiceSDK.chat_stream() — SDK 응답에 PATCH 태그 포함 → patch 이벤트 발행 + state 업데이트
UT-007-13: ChatServiceSDK.chat_stream() — 메시지 2000자 초과 → error 이벤트 발행
UT-007-14: ChatServiceSDK.chat_stream() — SSE 이벤트 구조가 ChatService와 동일
UT-007-15: routers/generate.py — 팩토리 반환 서비스의 generate_stream() 호출 여부
UT-007-16: routers/chat.py — 팩토리 반환 서비스의 chat_stream() 호출 여부
"""

import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import app.state as state
from app.models.requirement import DetailRequirement, OriginalRequirement
from app.models.api import ChatMessage


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
    ]


def _parse_events(events: list[str]) -> list[dict]:
    """SSE 이벤트 문자열 목록을 dict 목록으로 파싱한다."""
    result = []
    for e in events:
        raw = e.removeprefix("data: ").strip()
        if raw:
            result.append(json.loads(raw))
    return result


def _make_sdk_assistant_message(text: str):
    """claude_agent_sdk AssistantMessage mock을 생성한다."""
    from claude_agent_sdk import AssistantMessage, TextBlock

    block = TextBlock(text=text)
    msg = MagicMock(spec=AssistantMessage)
    msg.__class__ = AssistantMessage
    msg.content = [block]
    return msg


def _make_sdk_result_message(result: str = ""):
    """claude_agent_sdk ResultMessage mock을 생성한다."""
    from claude_agent_sdk import ResultMessage

    msg = MagicMock(spec=ResultMessage)
    msg.__class__ = ResultMessage
    msg.result = result
    return msg


def _make_sdk_stream(messages: list):
    """query()가 반환하는 async iterator mock을 생성한다."""
    async def _stream():
        for msg in messages:
            yield msg

    return _stream()


# ---------------------------------------------------------------------------
# UT-007-01~06: 팩토리 테스트
# ---------------------------------------------------------------------------


class TestAiBackendFactory:
    """UT-007-01~06: ai_backend_factory.py의 팩토리 함수 테스트."""

    def test_ut_007_01_anthropic_api_returns_ai_generate_service(self):
        """UT-007-01: AI_BACKEND=anthropic_api → AiGenerateService 인스턴스 반환."""
        from app.services.ai_generate_service import AiGenerateService
        from app.services.ai_backend_factory import get_ai_generate_service

        with patch.dict(os.environ, {"AI_BACKEND": "anthropic_api"}):
            service = get_ai_generate_service()

        assert isinstance(service, AiGenerateService)

    def test_ut_007_02_claude_code_sdk_returns_sdk_generate_service(self):
        """UT-007-02: AI_BACKEND=claude_code_sdk → AIGenerateServiceSDK 인스턴스 반환."""
        from app.services.ai_generate_service_sdk import AIGenerateServiceSDK
        from app.services.ai_backend_factory import get_ai_generate_service

        with patch.dict(os.environ, {"AI_BACKEND": "claude_code_sdk"}):
            service = get_ai_generate_service()

        assert isinstance(service, AIGenerateServiceSDK)

    def test_ut_007_03_no_env_defaults_to_sdk_generate_service(self):
        """UT-007-03: AI_BACKEND 미설정(기본값) → AIGenerateServiceSDK 인스턴스 반환."""
        from app.services.ai_generate_service_sdk import AIGenerateServiceSDK
        from app.services.ai_backend_factory import get_ai_generate_service

        env = {k: v for k, v in os.environ.items() if k != "AI_BACKEND"}
        with patch.dict(os.environ, env, clear=True):
            service = get_ai_generate_service()

        assert isinstance(service, AIGenerateServiceSDK)

    def test_ut_007_04_invalid_value_falls_back_to_sdk_no_crash(self):
        """UT-007-04: AI_BACKEND=invalid_value → AIGenerateServiceSDK 폴백 반환, 앱 크래시 없음."""
        from app.services.ai_generate_service_sdk import AIGenerateServiceSDK
        from app.services.ai_backend_factory import get_ai_generate_service

        with patch.dict(os.environ, {"AI_BACKEND": "invalid_value"}):
            service = get_ai_generate_service()  # 예외 발생하지 않아야 한다

        assert isinstance(service, AIGenerateServiceSDK)

    def test_ut_007_05_anthropic_api_returns_chat_service(self):
        """UT-007-05: AI_BACKEND=anthropic_api → ChatService 인스턴스 반환."""
        from app.services.chat_service import ChatService
        from app.services.ai_backend_factory import get_chat_service

        with patch.dict(os.environ, {"AI_BACKEND": "anthropic_api"}):
            service = get_chat_service()

        assert isinstance(service, ChatService)

    def test_ut_007_06_claude_code_sdk_returns_chat_service_sdk(self):
        """UT-007-06: AI_BACKEND=claude_code_sdk → ChatServiceSDK 인스턴스 반환."""
        from app.services.chat_service_sdk import ChatServiceSDK
        from app.services.ai_backend_factory import get_chat_service

        with patch.dict(os.environ, {"AI_BACKEND": "claude_code_sdk"}):
            service = get_chat_service()

        assert isinstance(service, ChatServiceSDK)


# ---------------------------------------------------------------------------
# UT-007-07~10: AIGenerateServiceSDK 테스트
# ---------------------------------------------------------------------------


class TestAIGenerateServiceSDK:
    """UT-007-07~10: AIGenerateServiceSDK.generate_stream() 테스트."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())

    @pytest.mark.asyncio
    async def test_ut_007_07_normal_response_emits_item_events(self):
        """UT-007-07: SDK 정상 응답 → item 이벤트 1건 이상 발행."""
        from app.services.ai_generate_service_sdk import AIGenerateServiceSDK

        item_json = json.dumps({
            "id": "SFR-001-01",
            "parent_id": "SFR-001",
            "category": "기능",
            "name": "UI",
            "content": "드래그앤드롭",
        }, ensure_ascii=False)

        sdk_messages = [
            _make_sdk_assistant_message(f"[{item_json}]"),
            _make_sdk_result_message(""),
        ]

        service = AIGenerateServiceSDK()
        with patch("app.services.ai_generate_service_sdk.query", return_value=_make_sdk_stream(sdk_messages)):
            events = []
            async for event in service.generate_stream("test-session", _REQ_GROUP):
                events.append(event)

        parsed = _parse_events(events)
        item_events = [e for e in parsed if e["type"] == "item"]
        assert len(item_events) >= 1, "item 이벤트가 1건 이상 발행되어야 한다"

    @pytest.mark.asyncio
    async def test_ut_007_08_item_event_has_same_keys_as_ai_generate_service(self):
        """UT-007-08: SSE item 이벤트 구조가 AiGenerateService와 동일한 JSON 키를 포함."""
        from app.services.ai_generate_service_sdk import AIGenerateServiceSDK

        item_json = json.dumps({
            "id": "SFR-001-01",
            "parent_id": "SFR-001",
            "category": "기능",
            "name": "UI",
            "content": "드래그앤드롭",
        }, ensure_ascii=False)

        sdk_messages = [
            _make_sdk_assistant_message(f"[{item_json}]"),
            _make_sdk_result_message(""),
        ]

        service = AIGenerateServiceSDK()
        with patch("app.services.ai_generate_service_sdk.query", return_value=_make_sdk_stream(sdk_messages)):
            events = []
            async for event in service.generate_stream("test-session", _REQ_GROUP):
                events.append(event)

        parsed = _parse_events(events)
        item_events = [e for e in parsed if e["type"] == "item"]
        assert len(item_events) >= 1

        # AiGenerateService가 발행하는 item 이벤트의 data 키 확인
        expected_keys = {"id", "parent_id", "category", "name", "content", "order_index", "is_modified"}
        item = item_events[0]
        assert "data" in item, "item 이벤트에 'data' 키가 있어야 한다"
        assert expected_keys.issubset(item["data"].keys()), (
            f"item.data에 필수 키가 모두 있어야 한다. 누락: {expected_keys - item['data'].keys()}"
        )

    @pytest.mark.asyncio
    async def test_ut_007_09_sdk_exception_emits_error_event_no_crash(self):
        """UT-007-09: SDK 예외 발생 → error SSE 이벤트 발행 (앱 크래시 없음)."""
        from app.services.ai_generate_service_sdk import AIGenerateServiceSDK

        async def _failing_query(*args, **kwargs):
            raise RuntimeError("SDK 오류 시뮬레이션")
            yield  # AsyncGenerator 타입 힌트를 위한 더미

        service = AIGenerateServiceSDK()
        with patch("app.services.ai_generate_service_sdk.query", new=_failing_query):
            events = []
            async for event in service.generate_stream("test-session", _REQ_GROUP):
                events.append(event)  # 예외가 전파되지 않아야 한다

        parsed = _parse_events(events)
        assert len(parsed) >= 1
        assert parsed[-1]["type"] == "error", "마지막 이벤트가 error여야 한다"
        assert "message" in parsed[-1]

    @pytest.mark.asyncio
    async def test_ut_007_10_no_originals_emits_error_event(self):
        """UT-007-10: 원본 요구사항 없을 때 → error SSE 이벤트 발행."""
        from app.services.ai_generate_service_sdk import AIGenerateServiceSDK

        state.reset_session()  # 원본 없는 상태

        service = AIGenerateServiceSDK()
        events = []
        async for event in service.generate_stream("test-session", _REQ_GROUP):
            events.append(event)

        parsed = _parse_events(events)
        assert len(parsed) == 1
        assert parsed[0]["type"] == "error"


# ---------------------------------------------------------------------------
# UT-007-11~14: ChatServiceSDK 테스트
# ---------------------------------------------------------------------------


class TestChatServiceSDK:
    """UT-007-11~14: ChatServiceSDK.chat_stream() 테스트."""

    def setup_method(self):
        state.reset_session()
        state.set_original(_make_originals())
        state.set_detail(_make_details())

    @pytest.mark.asyncio
    async def test_ut_007_11_normal_response_emits_text_event(self):
        """UT-007-11: SDK 정상 응답 → text 이벤트 발행."""
        from app.services.chat_service_sdk import ChatServiceSDK

        sdk_messages = [
            _make_sdk_assistant_message("요청하신 내용을 확인했습니다."),
            _make_sdk_result_message(""),
        ]

        service = ChatServiceSDK()
        with patch("app.services.chat_service_sdk.query", return_value=_make_sdk_stream(sdk_messages)):
            events = []
            async for event in service.chat_stream("test-session", "설명해줘", [], _REQ_GROUP):
                events.append(event)

        parsed = _parse_events(events)
        text_events = [e for e in parsed if e["type"] == "text"]
        assert len(text_events) >= 1, "text 이벤트가 1건 이상 발행되어야 한다"

    @pytest.mark.asyncio
    async def test_ut_007_12_patch_tag_emits_patch_event_and_updates_state(self):
        """UT-007-12: SDK 응답에 PATCH 태그 포함 → patch 이벤트 발행 + state 업데이트."""
        from app.services.chat_service_sdk import ChatServiceSDK

        patch_json = json.dumps(
            {"id": "SFR-001-01", "field": "content", "value": "수정된 내용"}
        )
        response_text = f"수정했습니다. <PATCH>{patch_json}</PATCH>"

        sdk_messages = [
            _make_sdk_assistant_message(response_text),
            _make_sdk_result_message(""),
        ]

        service = ChatServiceSDK()
        with patch("app.services.chat_service_sdk.query", return_value=_make_sdk_stream(sdk_messages)):
            events = []
            async for event in service.chat_stream("test-session", "수정해줘", [], _REQ_GROUP):
                events.append(event)

        parsed = _parse_events(events)
        patch_events = [e for e in parsed if e["type"] == "patch"]
        assert len(patch_events) >= 1, "patch 이벤트가 1건 이상 발행되어야 한다"

        # state가 실제로 업데이트되었는지 확인
        details = state.get_detail()
        target = next((d for d in details if d.id == "SFR-001-01"), None)
        assert target is not None
        assert target.content == "수정된 내용", "state의 content가 수정되어야 한다"

    @pytest.mark.asyncio
    async def test_ut_007_13_message_too_long_emits_error_event(self):
        """UT-007-13: 메시지 2000자 초과 → error 이벤트 발행 (SEC-007-02)."""
        from app.services.chat_service_sdk import ChatServiceSDK
        from app.services.chat_service import MAX_MESSAGE_LENGTH

        long_message = "a" * (MAX_MESSAGE_LENGTH + 1)

        service = ChatServiceSDK()
        events = []
        async for event in service.chat_stream("test-session", long_message, [], _REQ_GROUP):
            events.append(event)

        parsed = _parse_events(events)
        assert len(parsed) == 1
        assert parsed[0]["type"] == "error"
        assert str(MAX_MESSAGE_LENGTH) in parsed[0]["message"]

    @pytest.mark.asyncio
    async def test_ut_007_14_event_structure_matches_chat_service(self):
        """UT-007-14: SSE 이벤트 구조가 ChatService와 동일한 JSON 키를 포함."""
        from app.services.chat_service_sdk import ChatServiceSDK

        patch_json = json.dumps(
            {"id": "SFR-001-01", "field": "name", "value": "새 이름"}
        )
        response_text = f"처리했습니다. <PATCH>{patch_json}</PATCH>"

        sdk_messages = [
            _make_sdk_assistant_message(response_text),
            _make_sdk_result_message(""),
        ]

        service = ChatServiceSDK()
        with patch("app.services.chat_service_sdk.query", return_value=_make_sdk_stream(sdk_messages)):
            events = []
            async for event in service.chat_stream("test-session", "수정", [], _REQ_GROUP):
                events.append(event)

        parsed = _parse_events(events)

        # text 이벤트 구조 확인
        text_events = [e for e in parsed if e["type"] == "text"]
        for te in text_events:
            assert "delta" in te, "text 이벤트에 'delta' 키가 있어야 한다"

        # patch 이벤트 구조 확인
        patch_events = [e for e in parsed if e["type"] == "patch"]
        for pe in patch_events:
            assert "id" in pe, "patch 이벤트에 'id' 키가 있어야 한다"
            assert "field" in pe, "patch 이벤트에 'field' 키가 있어야 한다"
            assert "value" in pe, "patch 이벤트에 'value' 키가 있어야 한다"

        # done 이벤트가 마지막으로 발행되어야 한다
        assert parsed[-1]["type"] == "done", "마지막 이벤트가 done이어야 한다"


# ---------------------------------------------------------------------------
# UT-007-15~16: 라우터 팩토리 호출 테스트
# ---------------------------------------------------------------------------


class TestRouterFactoryIntegration:
    """UT-007-15~16: 라우터가 팩토리 반환 서비스를 올바르게 호출하는지 확인."""

    @pytest.mark.asyncio
    async def test_ut_007_15_generate_router_calls_factory_service(self):
        """UT-007-15: generate 라우터가 팩토리 반환 서비스의 generate_stream()을 호출한다."""
        mock_service = MagicMock()

        async def _mock_stream(session_id, req_group=""):
            yield "data: {}\n\n"

        mock_service.generate_stream = _mock_stream

        with patch("app.routers.generate.get_ai_generate_service", return_value=mock_service):
            from app.routers.generate import generate_details
            from app.models.api import GenerateRequest

            req = GenerateRequest(session_id="test-session", req_group="SFR-001")
            response = await generate_details(req)

            # StreamingResponse가 반환되어야 한다
            assert response is not None
            assert response.media_type == "text/event-stream"

    @pytest.mark.asyncio
    async def test_ut_007_16_chat_router_calls_factory_service(self):
        """UT-007-16: chat 라우터가 팩토리 반환 서비스의 chat_stream()을 호출한다."""
        mock_service = MagicMock()

        async def _mock_stream(session_id, message, history, req_group=""):
            yield "data: {}\n\n"

        mock_service.chat_stream = _mock_stream

        with patch("app.routers.chat.get_chat_service", return_value=mock_service):
            from app.routers.chat import chat
            from app.models.api import ChatRequest

            req = ChatRequest(session_id="test-session", message="테스트", history=[], req_group="SFR-001")
            response = await chat(req)

            assert response is not None
            assert response.media_type == "text/event-stream"
