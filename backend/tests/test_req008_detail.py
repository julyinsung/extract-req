"""REQ-008 인라인 편집 서버 동기화 단위 테스트.

UT-008-01: 유효한 id와 field로 요청 시 수정된 DetailRequirement 반환 (200)
UT-008-02: 존재하지 않는 id로 요청 시 404 반환
UT-008-03: field 값이 허용 범위 외이면 422 반환
UT-008-04: 수정 후 state.get_detail()에서 해당 항목의 값이 변경되어 있음
UT-008-05: 수정 후 해당 항목의 is_modified가 True로 설정됨

실제 DB 없이 인메모리 state를 직접 조작하며, FastAPI TestClient로 HTTP 계층을 통합 검증한다.
"""

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
    # set_detail()은 status를 'generated'로 전이시키므로 상세요구사항 등록에 사용한다.
    state.set_detail(_make_details())


# ---------------------------------------------------------------------------
# UT-008-01: 유효한 id와 field로 요청 시 수정된 DetailRequirement 반환 (200)
# ---------------------------------------------------------------------------


class TestPatchDetailSuccess:
    """UT-008-01: 정상 요청 시 200과 수정된 DetailRequirement를 반환해야 한다."""

    def setup_method(self):
        setup_state_with_details()

    def test_returns_200_with_updated_detail(self):
        """content 필드 수정 요청 시 200과 갱신된 항목을 반환해야 한다."""
        payload = {
            "detail_id": "REQ-001-01",
            "field": "content",
            "value": "수정된 내용 텍스트",
        }
        response = client.patch("/api/v1/detail/REQ-001-01", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == "REQ-001-01"
        assert body["content"] == "수정된 내용 텍스트"

    def test_returns_updated_name_field(self):
        """name 필드 수정 요청 시 응답의 name이 새 값이어야 한다."""
        payload = {
            "detail_id": "REQ-001-02",
            "field": "name",
            "value": "수정된 명칭",
        }
        response = client.patch("/api/v1/detail/REQ-001-02", json=payload)

        assert response.status_code == 200
        assert response.json()["name"] == "수정된 명칭"

    def test_returns_updated_category_field(self):
        """category 필드 수정 요청 시 응답의 category가 새 값이어야 한다."""
        payload = {
            "detail_id": "REQ-001-01",
            "field": "category",
            "value": "비기능 요구사항",
        }
        response = client.patch("/api/v1/detail/REQ-001-01", json=payload)

        assert response.status_code == 200
        assert response.json()["category"] == "비기능 요구사항"


# ---------------------------------------------------------------------------
# UT-008-02: 존재하지 않는 id로 요청 시 404 반환
# ---------------------------------------------------------------------------


class TestPatchDetailNotFound:
    """UT-008-02: 존재하지 않는 id 요청 시 404와 NOT_FOUND 코드를 반환해야 한다."""

    def setup_method(self):
        setup_state_with_details()

    def test_returns_404_for_unknown_id(self):
        """존재하지 않는 id로 요청 시 404를 반환해야 한다."""
        payload = {
            "detail_id": "REQ-999-99",
            "field": "content",
            "value": "값",
        }
        response = client.patch("/api/v1/detail/REQ-999-99", json=payload)

        assert response.status_code == 404

    def test_404_response_contains_not_found_code(self):
        """404 응답 바디에 code: NOT_FOUND가 포함되어야 한다."""
        payload = {
            "detail_id": "REQ-999-99",
            "field": "content",
            "value": "값",
        }
        response = client.patch("/api/v1/detail/REQ-999-99", json=payload)

        body = response.json()
        # FastAPI HTTPException detail은 response.json()["detail"]에 위치한다.
        assert body["detail"]["code"] == "NOT_FOUND"

    def test_404_when_state_is_empty(self):
        """상세요구사항이 없는 상태에서 요청 시 404를 반환해야 한다."""
        state.reset_session()  # 상세요구사항 없이 빈 세션
        payload = {
            "detail_id": "REQ-001-01",
            "field": "content",
            "value": "값",
        }
        response = client.patch("/api/v1/detail/REQ-001-01", json=payload)

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# UT-008-03: field 값이 허용 범위 외이면 422 반환
# ---------------------------------------------------------------------------


class TestPatchDetailInvalidField:
    """UT-008-03: 허용되지 않는 field 값 요청 시 Pydantic 422를 반환해야 한다."""

    def setup_method(self):
        setup_state_with_details()

    def test_returns_422_for_id_field(self):
        """field='id' (내부 식별자) 요청 시 422를 반환해야 한다 (SEC-008-01)."""
        payload = {
            "detail_id": "REQ-001-01",
            "field": "id",
            "value": "조작된-ID",
        }
        response = client.patch("/api/v1/detail/REQ-001-01", json=payload)

        assert response.status_code == 422

    def test_returns_422_for_parent_id_field(self):
        """field='parent_id' 요청 시 422를 반환해야 한다 (SEC-008-01)."""
        payload = {
            "detail_id": "REQ-001-01",
            "field": "parent_id",
            "value": "조작된-부모",
        }
        response = client.patch("/api/v1/detail/REQ-001-01", json=payload)

        assert response.status_code == 422

    def test_returns_422_for_is_modified_field(self):
        """field='is_modified' 요청 시 422를 반환해야 한다 (SEC-008-01)."""
        payload = {
            "detail_id": "REQ-001-01",
            "field": "is_modified",
            "value": "false",
        }
        response = client.patch("/api/v1/detail/REQ-001-01", json=payload)

        assert response.status_code == 422

    def test_returns_422_for_arbitrary_field(self):
        """임의의 field 값 요청 시 422를 반환해야 한다 (SEC-008-01)."""
        payload = {
            "detail_id": "REQ-001-01",
            "field": "arbitrary_field",
            "value": "값",
        }
        response = client.patch("/api/v1/detail/REQ-001-01", json=payload)

        assert response.status_code == 422

    def test_state_unchanged_after_invalid_field(self):
        """422 응답 후 state의 해당 항목이 변경되지 않아야 한다 (SEC-008-01)."""
        original_content = state.get_detail()[0].content
        payload = {
            "detail_id": "REQ-001-01",
            "field": "order_index",
            "value": "999",
        }
        client.patch("/api/v1/detail/REQ-001-01", json=payload)

        assert state.get_detail()[0].content == original_content


# ---------------------------------------------------------------------------
# UT-008-04: 수정 후 state.get_detail()에서 해당 항목의 값이 변경되어 있음
# ---------------------------------------------------------------------------


class TestPatchDetailStateUpdate:
    """UT-008-04: PATCH 성공 후 state에 변경 내용이 반영되어야 한다."""

    def setup_method(self):
        setup_state_with_details()

    def test_state_reflects_updated_content(self):
        """PATCH 후 state.get_detail()의 해당 항목 content가 새 값이어야 한다."""
        new_content = "state 반영 검증용 새 내용"
        payload = {
            "detail_id": "REQ-001-01",
            "field": "content",
            "value": new_content,
        }
        client.patch("/api/v1/detail/REQ-001-01", json=payload)

        details = state.get_detail()
        target = next(d for d in details if d.id == "REQ-001-01")
        assert target.content == new_content

    def test_other_items_not_affected(self):
        """한 항목 수정 후 다른 항목의 content는 변경되지 않아야 한다."""
        original_content = next(
            d.content for d in state.get_detail() if d.id == "REQ-001-02"
        )
        payload = {
            "detail_id": "REQ-001-01",
            "field": "content",
            "value": "REQ-001-01 전용 수정",
        }
        client.patch("/api/v1/detail/REQ-001-01", json=payload)

        unchanged = next(d for d in state.get_detail() if d.id == "REQ-001-02")
        assert unchanged.content == original_content


# ---------------------------------------------------------------------------
# UT-008-05: 수정 후 해당 항목의 is_modified가 True로 설정됨
# ---------------------------------------------------------------------------


class TestPatchDetailIsModified:
    """UT-008-05: PATCH 성공 후 해당 항목의 is_modified가 True여야 한다."""

    def setup_method(self):
        setup_state_with_details()

    def test_is_modified_set_to_true_in_response(self):
        """200 응답 바디의 is_modified가 True여야 한다."""
        payload = {
            "detail_id": "REQ-001-01",
            "field": "content",
            "value": "수정 완료",
        }
        response = client.patch("/api/v1/detail/REQ-001-01", json=payload)

        assert response.status_code == 200
        assert response.json()["is_modified"] is True

    def test_is_modified_set_to_true_in_state(self):
        """PATCH 후 state의 해당 항목 is_modified가 True여야 한다."""
        payload = {
            "detail_id": "REQ-001-02",
            "field": "name",
            "value": "수정된 명칭",
        }
        client.patch("/api/v1/detail/REQ-001-02", json=payload)

        target = next(d for d in state.get_detail() if d.id == "REQ-001-02")
        assert target.is_modified is True

    def test_unmodified_item_is_modified_remains_false(self):
        """수정하지 않은 항목의 is_modified는 False로 유지되어야 한다."""
        payload = {
            "detail_id": "REQ-001-01",
            "field": "content",
            "value": "REQ-001-01만 수정",
        }
        client.patch("/api/v1/detail/REQ-001-01", json=payload)

        # REQ-001-02는 수정하지 않았으므로 is_modified가 False여야 한다.
        untouched = next(d for d in state.get_detail() if d.id == "REQ-001-02")
        assert untouched.is_modified is False


# ---------------------------------------------------------------------------
# 보안 테스트: SEC-008-03 value 길이 제한
# ---------------------------------------------------------------------------


class TestPatchDetailValueLengthLimit:
    """SEC-008-03: value가 MAX_VALUE_LENGTH(5000자)를 초과하면 422를 반환해야 한다."""

    def setup_method(self):
        setup_state_with_details()

    def test_returns_422_for_oversized_value(self):
        """5001자 value 요청 시 422를 반환해야 한다 (SEC-008-03)."""
        from app.routers.detail import MAX_VALUE_LENGTH

        payload = {
            "detail_id": "REQ-001-01",
            "field": "content",
            "value": "a" * (MAX_VALUE_LENGTH + 1),
        }
        response = client.patch("/api/v1/detail/REQ-001-01", json=payload)

        assert response.status_code == 422

    def test_state_unchanged_after_oversized_value(self):
        """5001자 value 요청 후 state는 변경되지 않아야 한다 (SEC-008-03)."""
        from app.routers.detail import MAX_VALUE_LENGTH

        original_content = next(
            d.content for d in state.get_detail() if d.id == "REQ-001-01"
        )
        payload = {
            "detail_id": "REQ-001-01",
            "field": "content",
            "value": "a" * (MAX_VALUE_LENGTH + 1),
        }
        client.patch("/api/v1/detail/REQ-001-01", json=payload)

        assert (
            next(d.content for d in state.get_detail() if d.id == "REQ-001-01")
            == original_content
        )
