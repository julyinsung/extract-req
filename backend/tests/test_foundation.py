"""백엔드 기반 구조 단위 테스트.

UT-006-02: 파서 파일 import 성공 확인
UT-006-03: SessionStore 저장/조회/reset 정상 동작 확인
"""

import pytest


class TestParserImport:
    """UT-006-02: 파서 파일 재활용 — import 성공 확인."""

    def test_hwp_ole_reader_import(self):
        """HWPOLEReader 클래스를 import할 수 있어야 한다."""
        from app.parser.hwp_ole_reader import HWPOLEReader

        assert HWPOLEReader is not None

    def test_hwp_body_parser_import(self):
        """HwpBodyParser 클래스를 import할 수 있어야 한다."""
        from app.parser.hwp_body_parser import HwpBodyParser

        assert HwpBodyParser is not None

    def test_hwp_ole_reader_has_required_methods(self):
        """HWPOLEReader가 필요한 메서드를 보유해야 한다."""
        from app.parser.hwp_ole_reader import HWPOLEReader

        assert hasattr(HWPOLEReader, "open")
        assert hasattr(HWPOLEReader, "get_bodytext_streams")
        assert hasattr(HWPOLEReader, "get_stream_data")
        assert hasattr(HWPOLEReader, "close")

    def test_hwp_body_parser_has_required_methods(self):
        """HwpBodyParser가 필요한 메서드를 보유해야 한다."""
        from app.parser.hwp_body_parser import HwpBodyParser

        assert hasattr(HwpBodyParser, "extract_text")
        assert hasattr(HwpBodyParser, "extract_all")


class TestSessionStore:
    """UT-006-03: SessionStore 저장/조회/reset 정상 동작 확인."""

    def setup_method(self):
        """각 테스트 전 세션을 초기 상태로 리셋한다.

        테스트 간 상태 오염을 방지하기 위해 매 테스트 전 reset_session()을 호출한다.
        """
        import app.state as state_module

        state_module.reset_session()

    def test_reset_session_returns_new_session(self):
        """reset_session()이 session_id를 가진 새 SessionState를 반환해야 한다."""
        from app.state import reset_session

        session = reset_session()

        assert session is not None
        assert session.session_id is not None
        assert len(session.session_id) > 0

    def test_get_session_returns_same_instance(self):
        """get_session()을 반복 호출해도 동일한 session_id를 반환해야 한다."""
        from app.state import get_session

        session1 = get_session()
        session2 = get_session()

        assert session1.session_id == session2.session_id

    def test_reset_creates_new_session_id(self):
        """reset_session() 호출 후 session_id가 이전과 달라야 한다."""
        from app.state import get_session, reset_session

        original_id = get_session().session_id
        reset_session()
        new_id = get_session().session_id

        assert original_id != new_id

    def test_initial_status_is_idle(self):
        """초기 세션 상태는 'idle'이어야 한다."""
        from app.state import get_session

        session = get_session()

        assert session.status == "idle"

    def test_set_original_stores_requirements(self):
        """set_original() 호출 후 get_original()로 동일한 데이터를 조회할 수 있어야 한다."""
        from app.models.requirement import OriginalRequirement
        from app.state import get_original, get_session, set_original

        reqs = [
            OriginalRequirement(
                id="REQ-001",
                category="기능요구사항",
                name="파일 업로드",
                content="사용자는 HWP 파일을 업로드할 수 있다.",
                order_index=0,
            )
        ]
        set_original(reqs)

        result = get_original()
        assert len(result) == 1
        assert result[0].id == "REQ-001"

    def test_set_original_changes_status_to_parsed(self):
        """set_original() 호출 후 세션 상태가 'parsed'로 전이되어야 한다."""
        from app.models.requirement import OriginalRequirement
        from app.state import get_session, set_original

        reqs = [
            OriginalRequirement(
                id="REQ-001",
                category="기능요구사항",
                name="파일 업로드",
                content="사용자는 HWP 파일을 업로드할 수 있다.",
                order_index=0,
            )
        ]
        set_original(reqs)

        assert get_session().status == "parsed"

    def test_patch_detail_modifies_field(self):
        """patch_detail() 호출 후 해당 필드가 수정되고 is_modified가 True가 되어야 한다."""
        from app.models.requirement import DetailRequirement
        from app.state import get_detail, patch_detail, set_detail

        reqs = [
            DetailRequirement(
                id="REQ-001-01",
                parent_id="REQ-001",
                category="기능요구사항",
                name="파일 선택 UI",
                content="드래그앤드롭 영역을 제공한다.",
                order_index=0,
            )
        ]
        set_detail(reqs)

        result = patch_detail("REQ-001-01", "name", "수정된 파일 선택 UI")

        assert result is True
        detail = get_detail()[0]
        assert detail.name == "수정된 파일 선택 UI"
        assert detail.is_modified is True

    def test_patch_detail_returns_false_for_unknown_id(self):
        """존재하지 않는 id로 patch_detail()을 호출하면 False를 반환해야 한다."""
        from app.state import patch_detail

        result = patch_detail("REQ-999-99", "name", "없는 항목")

        assert result is False

    def test_set_detail_changes_status_to_generated(self):
        """set_detail() 호출 후 세션 상태가 'generated'로 전이되어야 한다."""
        from app.models.requirement import DetailRequirement
        from app.state import get_session, set_detail

        reqs = [
            DetailRequirement(
                id="REQ-001-01",
                parent_id="REQ-001",
                category="기능요구사항",
                name="파일 선택 UI",
                content="드래그앤드롭 영역을 제공한다.",
                order_index=0,
            )
        ]
        set_detail(reqs)

        assert get_session().status == "generated"

    def test_reset_clears_requirements(self):
        """reset_session() 후 원본/상세 요구사항이 빈 리스트여야 한다."""
        from app.models.requirement import OriginalRequirement
        from app.state import get_original, reset_session, set_original

        reqs = [
            OriginalRequirement(
                id="REQ-001",
                category="기능요구사항",
                name="파일 업로드",
                content="사용자는 HWP 파일을 업로드할 수 있다.",
                order_index=0,
            )
        ]
        set_original(reqs)
        reset_session()

        assert get_original() == []
