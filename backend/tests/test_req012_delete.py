"""REQ-012 상세요구사항 행 삭제 백엔드 단위 테스트.

UT-012-01: state.delete_detail() — 존재하는 id 삭제 시 True 반환 및 목록에서 제거
UT-012-02: state.delete_detail() — 존재하지 않는 id 삭제 시 False 반환
UT-012-03: DELETE /api/v1/detail/{id} — 존재하는 id 요청 시 200 + {"deleted_id": id} 반환
UT-012-04: DELETE /api/v1/detail/{id} — 존재하지 않는 id 요청 시 404 반환

실제 DB 없이 인메모리 state를 직접 조작하며, FastAPI TestClient로 HTTP 계층을 통합 검증한다.
snapshot 저장은 save_snapshot()을 patch하여 파일 시스템 의존성을 제거한다.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import app.state as state
from app.main import app
from app.models.requirement import DetailRequirement, OriginalRequirement

client = TestClient(app)


# ---------------------------------------------------------------------------
# 픽스처 헬퍼
# ---------------------------------------------------------------------------


def _make_details() -> list[DetailRequirement]:
    """테스트용 상세요구사항 픽스처 — 2건."""
    return [
        DetailRequirement(
            id="REQ-001-01",
            parent_id="REQ-001",
            category="기능 요구사항",
            name="로그인 기능",
            content="사용자는 ID/PW로 로그인할 수 있다.",
            order_index=0,
            is_modified=False,
        ),
        DetailRequirement(
            id="REQ-001-02",
            parent_id="REQ-001",
            category="기능 요구사항",
            name="로그아웃 기능",
            content="사용자는 로그아웃할 수 있다.",
            order_index=1,
            is_modified=False,
        ),
    ]


def setup_state_with_details() -> None:
    """state를 초기화하고 픽스처 상세요구사항을 적재한다."""
    state.reset_session()
    state.set_original(
        [
            OriginalRequirement(
                id="REQ-001",
                category="기능 요구사항",
                name="인증",
                content="인증 관련 요구사항",
                order_index=0,
            )
        ]
    )
    # snapshot 저장을 억제하여 파일 시스템 의존성 제거
    with patch("app.snapshot.save_snapshot"):
        state.set_detail(_make_details())


# ---------------------------------------------------------------------------
# UT-012-01: state.delete_detail() — 존재하는 id 삭제 시 True 반환 및 목록에서 제거
# ---------------------------------------------------------------------------


class TestDeleteDetailSuccess:
    """UT-012-01: 존재하는 id 삭제 시 True 반환 및 목록에서 제거되어야 한다."""

    def setup_method(self):
        setup_state_with_details()

    def test_returns_true_for_existing_id(self):
        """존재하는 id 삭제 시 True를 반환해야 한다."""
        with patch("app.snapshot.save_snapshot"):
            result = state.delete_detail("REQ-001-01")

        assert result is True

    def test_item_removed_from_state(self):
        """삭제 후 state.get_detail()에서 해당 항목이 없어야 한다."""
        with patch("app.snapshot.save_snapshot"):
            state.delete_detail("REQ-001-01")

        ids = [r.id for r in state.get_detail()]
        assert "REQ-001-01" not in ids

    def test_other_items_remain_intact(self):
        """삭제 후 다른 항목은 유지되어야 한다."""
        with patch("app.snapshot.save_snapshot"):
            state.delete_detail("REQ-001-01")

        ids = [r.id for r in state.get_detail()]
        assert "REQ-001-02" in ids

    def test_count_decreases_by_one(self):
        """삭제 후 목록 개수가 1 감소해야 한다."""
        before_count = len(state.get_detail())
        with patch("app.snapshot.save_snapshot"):
            state.delete_detail("REQ-001-01")

        assert len(state.get_detail()) == before_count - 1


# ---------------------------------------------------------------------------
# UT-012-02: state.delete_detail() — 존재하지 않는 id 삭제 시 False 반환
# ---------------------------------------------------------------------------


class TestDeleteDetailNotFound:
    """UT-012-02: 존재하지 않는 id 삭제 시 False를 반환해야 한다."""

    def setup_method(self):
        setup_state_with_details()

    def test_returns_false_for_unknown_id(self):
        """존재하지 않는 id 삭제 시 False를 반환해야 한다."""
        with patch("app.snapshot.save_snapshot"):
            result = state.delete_detail("REQ-999-99")

        assert result is False

    def test_state_unchanged_for_unknown_id(self):
        """존재하지 않는 id 삭제 시 state 목록이 변경되지 않아야 한다."""
        before_ids = [r.id for r in state.get_detail()]
        with patch("app.snapshot.save_snapshot"):
            state.delete_detail("REQ-999-99")

        assert [r.id for r in state.get_detail()] == before_ids

    def test_returns_false_on_empty_state(self):
        """상세요구사항이 없는 상태에서 삭제 시 False를 반환해야 한다."""
        state.reset_session()
        with patch("app.snapshot.save_snapshot"):
            result = state.delete_detail("REQ-001-01")

        assert result is False


# ---------------------------------------------------------------------------
# UT-012-03: DELETE /api/v1/detail/{id} — 존재하는 id 요청 시 200 반환
# ---------------------------------------------------------------------------


class TestDeleteEndpointSuccess:
    """UT-012-03: 존재하는 id 요청 시 200과 {"deleted_id": id}를 반환해야 한다."""

    def setup_method(self):
        setup_state_with_details()

    def test_returns_200_with_deleted_id(self):
        """존재하는 id로 DELETE 요청 시 200과 deleted_id를 반환해야 한다."""
        with patch("app.snapshot.save_snapshot"):
            response = client.delete("/api/v1/detail/REQ-001-01")

        assert response.status_code == 200
        assert response.json() == {"deleted_id": "REQ-001-01"}

    def test_item_removed_after_delete_request(self):
        """DELETE 요청 성공 후 state에서 해당 항목이 제거되어야 한다."""
        with patch("app.snapshot.save_snapshot"):
            client.delete("/api/v1/detail/REQ-001-01")

        ids = [r.id for r in state.get_detail()]
        assert "REQ-001-01" not in ids

    def test_returns_correct_deleted_id_in_body(self):
        """응답 바디의 deleted_id가 요청한 id와 일치해야 한다."""
        with patch("app.snapshot.save_snapshot"):
            response = client.delete("/api/v1/detail/REQ-001-02")

        assert response.json()["deleted_id"] == "REQ-001-02"


# ---------------------------------------------------------------------------
# UT-012-04: DELETE /api/v1/detail/{id} — 존재하지 않는 id 요청 시 404 반환
# ---------------------------------------------------------------------------


class TestDeleteEndpointNotFound:
    """UT-012-04: 존재하지 않는 id 요청 시 404와 NOT_FOUND 코드를 반환해야 한다."""

    def setup_method(self):
        setup_state_with_details()

    def test_returns_404_for_unknown_id(self):
        """존재하지 않는 id로 DELETE 요청 시 404를 반환해야 한다."""
        response = client.delete("/api/v1/detail/REQ-999-99")

        assert response.status_code == 404

    def test_404_response_contains_not_found_code(self):
        """404 응답 바디에 code: NOT_FOUND가 포함되어야 한다."""
        response = client.delete("/api/v1/detail/REQ-999-99")

        body = response.json()
        assert body["detail"]["code"] == "NOT_FOUND"

    def test_returns_404_when_state_empty(self):
        """상세요구사항이 없는 상태에서 DELETE 요청 시 404를 반환해야 한다."""
        state.reset_session()
        response = client.delete("/api/v1/detail/REQ-001-01")

        assert response.status_code == 404
