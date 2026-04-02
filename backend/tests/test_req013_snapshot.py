"""REQ-013 파일 스냅샷 저장 및 복원 단위 테스트.

UT-013-01: save_snapshot() — 저장 후 JSON 파일에 두 키 포함 확인
UT-013-02: save_snapshot() — 두 번 연속 호출 시 최신 1개로 덮어쓰임
UT-013-03: load_snapshot() — 유효한 파일 존재 시 state 복원
UT-013-04: load_snapshot() — 파일 없으면 False 반환, state 빈 상태
UT-013-05: load_snapshot() — 손상된 JSON이면 False 반환, 서버 기동 중단 없음
UT-013-06: patch_detail() — 수정 성공 후 JSON 파일 갱신 확인
UT-013-07: delete_detail() — 존재하는 id 삭제 시 True, state에서 제거
UT-013-08: delete_detail() — 존재하지 않는 id 삭제 시 False, state 불변
UT-013-09: delete_detail() — 삭제 후 JSON 파일에 해당 항목 미포함
UT-013-10: set_detail() — 호출 후 JSON 파일 항목 수가 state와 일치
UT-013-11: save_snapshot() — 파일 쓰기 실패 시 예외 억제, 호출자에 미전파
UT-013-12: DELETE /api/v1/detail/{id} — 존재하는 id로 200 + {"deleted_id": id}
UT-013-13: DELETE /api/v1/detail/{id} — 존재하지 않는 id로 404 + NOT_FOUND
UT-013-14: load_snapshot() — 복원 후 state.get_original()이 스냅샷 목록 반환

파일 시스템 격리: 각 테스트는 tmp_path fixture를 사용하여 SNAPSHOT_PATH를 임시 경로로 교체한다.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import app.snapshot as snapshot
import app.state as state
from app.main import app
from app.models.requirement import DetailRequirement, OriginalRequirement

client = TestClient(app)


# ---------------------------------------------------------------------------
# 픽스처 헬퍼
# ---------------------------------------------------------------------------


def _make_originals() -> list[OriginalRequirement]:
    """테스트용 원본 요구사항 픽스처 — 1건."""
    return [
        OriginalRequirement(
            id="REQ-001",
            category="기능 요구사항",
            name="인증",
            content="인증 관련 요구사항",
            order_index=0,
        )
    ]


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


@pytest.fixture
def isolated_snapshot(tmp_path):
    """SNAPSHOT_PATH를 tmp_path로 교체하여 테스트 간 파일 시스템 격리를 보장한다."""
    snap_path = tmp_path / "session_snapshot.json"
    tmp_file = tmp_path / "session_snapshot.tmp"
    original_snap = snapshot.SNAPSHOT_PATH
    original_tmp = snapshot._TMP_PATH

    snapshot.SNAPSHOT_PATH = snap_path
    snapshot._TMP_PATH = tmp_file

    state.reset_session()

    yield snap_path

    # 복원
    snapshot.SNAPSHOT_PATH = original_snap
    snapshot._TMP_PATH = original_tmp
    state.reset_session()


# ---------------------------------------------------------------------------
# UT-013-01: save_snapshot() — 저장 후 JSON 파일에 두 키 포함
# ---------------------------------------------------------------------------


class TestSaveSnapshotCreatesFile:
    """UT-013-01: save_snapshot() 호출 후 JSON 파일이 생성되고 두 키를 포함해야 한다."""

    def test_creates_json_with_two_keys(self, isolated_snapshot):
        """저장 후 파일에 original_requirements와 detail_requirements 키가 있어야 한다."""
        state.set_original(_make_originals())
        # set_detail 내부 snapshot 호출을 직접 실행 (isolated_snapshot 경로 사용)
        session = state.get_session()
        with state._lock:
            session.detail_requirements = _make_details()
            session.status = "generated"

        snapshot.save_snapshot()

        assert isolated_snapshot.exists()
        data = json.loads(isolated_snapshot.read_text(encoding="utf-8"))
        assert "original_requirements" in data
        assert "detail_requirements" in data

    def test_original_requirements_count_matches(self, isolated_snapshot):
        """저장된 original_requirements 수가 state와 일치해야 한다."""
        originals = _make_originals()
        state.set_original(originals)
        snapshot.save_snapshot()

        data = json.loads(isolated_snapshot.read_text(encoding="utf-8"))
        assert len(data["original_requirements"]) == len(originals)

    def test_detail_requirements_count_matches(self, isolated_snapshot):
        """저장된 detail_requirements 수가 state와 일치해야 한다."""
        state.set_original(_make_originals())
        session = state.get_session()
        details = _make_details()
        with state._lock:
            session.detail_requirements = details
            session.status = "generated"

        snapshot.save_snapshot()

        data = json.loads(isolated_snapshot.read_text(encoding="utf-8"))
        assert len(data["detail_requirements"]) == len(details)


# ---------------------------------------------------------------------------
# UT-013-02: save_snapshot() — 두 번 연속 호출 시 최신 1개로 덮어쓰임
# ---------------------------------------------------------------------------


class TestSaveSnapshotOverwrite:
    """UT-013-02: 두 번 연속 호출 시 파일이 최신 상태 1개로 덮어쓰여야 한다."""

    def test_second_save_overwrites_first(self, isolated_snapshot):
        """첫 번째 저장 후 detail을 변경하고 두 번째 저장 시 최신 데이터만 남아야 한다."""
        state.set_original(_make_originals())
        session = state.get_session()

        with state._lock:
            session.detail_requirements = _make_details()
            session.status = "generated"
        snapshot.save_snapshot()

        # 두 번째 저장: detail을 1건으로 축소
        with state._lock:
            session.detail_requirements = [_make_details()[0]]
        snapshot.save_snapshot()

        data = json.loads(isolated_snapshot.read_text(encoding="utf-8"))
        assert len(data["detail_requirements"]) == 1
        assert data["detail_requirements"][0]["id"] == "REQ-001-01"


# ---------------------------------------------------------------------------
# UT-013-03: load_snapshot() — 유효한 파일 존재 시 state 복원
# ---------------------------------------------------------------------------


class TestLoadSnapshotSuccess:
    """UT-013-03: 유효한 파일 존재 시 state를 복원하고 True를 반환해야 한다."""

    def test_returns_true_on_valid_file(self, isolated_snapshot):
        """유효한 스냅샷 파일 존재 시 load_snapshot()이 True를 반환해야 한다."""
        # 스냅샷 파일 직접 작성
        data = {
            "original_requirements": [o.model_dump() for o in _make_originals()],
            "detail_requirements": [d.model_dump() for d in _make_details()],
        }
        isolated_snapshot.write_text(json.dumps(data), encoding="utf-8")

        state.reset_session()
        result = snapshot.load_snapshot()

        assert result is True

    def test_detail_requirements_restored(self, isolated_snapshot):
        """복원 후 state.get_detail()이 스냅샷의 상세요구사항을 반환해야 한다."""
        details = _make_details()
        data = {
            "original_requirements": [o.model_dump() for o in _make_originals()],
            "detail_requirements": [d.model_dump() for d in details],
        }
        isolated_snapshot.write_text(json.dumps(data), encoding="utf-8")

        state.reset_session()
        snapshot.load_snapshot()

        restored = state.get_detail()
        assert len(restored) == len(details)
        assert restored[0].id == "REQ-001-01"
        assert restored[1].id == "REQ-001-02"


# ---------------------------------------------------------------------------
# UT-013-04: load_snapshot() — 파일 없으면 False 반환, state 빈 상태
# ---------------------------------------------------------------------------


class TestLoadSnapshotNoFile:
    """UT-013-04: 파일이 없으면 False를 반환하고 state가 빈 상태여야 한다."""

    def test_returns_false_when_no_file(self, isolated_snapshot):
        """스냅샷 파일이 없으면 False를 반환해야 한다."""
        assert not isolated_snapshot.exists()
        result = snapshot.load_snapshot()

        assert result is False

    def test_state_remains_empty_when_no_file(self, isolated_snapshot):
        """파일 없을 때 state.get_detail()이 빈 목록이어야 한다."""
        snapshot.load_snapshot()

        assert state.get_detail() == []


# ---------------------------------------------------------------------------
# UT-013-05: load_snapshot() — 손상된 JSON이면 False 반환
# ---------------------------------------------------------------------------


class TestLoadSnapshotCorrupted:
    """UT-013-05: 손상된 JSON이면 False를 반환하고 서버 기동을 중단하지 않아야 한다."""

    def test_returns_false_on_corrupted_json(self, isolated_snapshot):
        """손상된 JSON 파일 존재 시 False를 반환해야 한다."""
        isolated_snapshot.write_text("{ corrupted json !!!", encoding="utf-8")

        result = snapshot.load_snapshot()

        assert result is False

    def test_no_exception_raised_on_corrupted_json(self, isolated_snapshot):
        """손상된 파일 처리 시 예외가 호출자에 전파되지 않아야 한다."""
        isolated_snapshot.write_text("not-json", encoding="utf-8")

        # 예외 없이 완료되어야 한다
        result = snapshot.load_snapshot()
        assert result is False

    def test_state_empty_after_corrupted_json(self, isolated_snapshot):
        """손상된 파일 복원 실패 후 state.get_detail()이 빈 목록이어야 한다."""
        isolated_snapshot.write_text("{}", encoding="utf-8")  # 키 없는 빈 JSON
        state.reset_session()

        snapshot.load_snapshot()

        assert state.get_detail() == []


# ---------------------------------------------------------------------------
# UT-013-06: patch_detail() — 수정 성공 후 JSON 파일 갱신
# ---------------------------------------------------------------------------


class TestPatchDetailSnapshotSync:
    """UT-013-06: patch_detail() 수정 성공 후 JSON 파일의 해당 항목 필드가 갱신되어야 한다."""

    def test_snapshot_updated_after_patch(self, isolated_snapshot):
        """patch_detail() 성공 후 스냅샷 파일의 content가 새 값이어야 한다."""
        state.set_original(_make_originals())
        session = state.get_session()
        with state._lock:
            session.detail_requirements = _make_details()
            session.status = "generated"
        snapshot.save_snapshot()  # 초기 스냅샷 저장

        state.patch_detail("REQ-001-01", "content", "수정된 내용")

        data = json.loads(isolated_snapshot.read_text(encoding="utf-8"))
        target = next(d for d in data["detail_requirements"] if d["id"] == "REQ-001-01")
        assert target["content"] == "수정된 내용"


# ---------------------------------------------------------------------------
# UT-013-07: delete_detail() — 존재하는 id 삭제 시 True 반환, state에서 제거
# ---------------------------------------------------------------------------


class TestDeleteDetailStateSync:
    """UT-013-07: delete_detail() 성공 시 True를 반환하고 state에서 제거되어야 한다."""

    def test_returns_true_and_removes_from_state(self, isolated_snapshot):
        """존재하는 id 삭제 시 True 반환 및 state에서 해당 항목이 없어야 한다."""
        state.set_original(_make_originals())
        session = state.get_session()
        with state._lock:
            session.detail_requirements = _make_details()
            session.status = "generated"

        result = state.delete_detail("REQ-001-01")

        assert result is True
        ids = [r.id for r in state.get_detail()]
        assert "REQ-001-01" not in ids


# ---------------------------------------------------------------------------
# UT-013-08: delete_detail() — 존재하지 않는 id 삭제 시 False 반환, state 불변
# ---------------------------------------------------------------------------


class TestDeleteDetailUnknownId:
    """UT-013-08: 존재하지 않는 id 삭제 시 False를 반환하고 state가 변경되지 않아야 한다."""

    def test_returns_false_and_state_unchanged(self, isolated_snapshot):
        """존재하지 않는 id 삭제 시 False, state 불변이어야 한다."""
        state.set_original(_make_originals())
        session = state.get_session()
        with state._lock:
            session.detail_requirements = _make_details()
            session.status = "generated"

        before_ids = [r.id for r in state.get_detail()]
        result = state.delete_detail("REQ-999-99")

        assert result is False
        assert [r.id for r in state.get_detail()] == before_ids


# ---------------------------------------------------------------------------
# UT-013-09: delete_detail() — 삭제 후 JSON 파일에 해당 항목 미포함
# ---------------------------------------------------------------------------


class TestDeleteDetailSnapshotSync:
    """UT-013-09: delete_detail() 성공 후 스냅샷 파일에 해당 항목이 없어야 한다."""

    def test_snapshot_excludes_deleted_item(self, isolated_snapshot):
        """삭제 후 스냅샷 파일의 detail_requirements에 삭제된 id가 없어야 한다."""
        state.set_original(_make_originals())
        session = state.get_session()
        with state._lock:
            session.detail_requirements = _make_details()
            session.status = "generated"
        snapshot.save_snapshot()  # 초기 스냅샷

        state.delete_detail("REQ-001-01")

        data = json.loads(isolated_snapshot.read_text(encoding="utf-8"))
        ids = [d["id"] for d in data["detail_requirements"]]
        assert "REQ-001-01" not in ids
        assert "REQ-001-02" in ids


# ---------------------------------------------------------------------------
# UT-013-10: set_detail() — 호출 후 JSON 파일 항목 수가 state와 일치
# ---------------------------------------------------------------------------


class TestSetDetailSnapshotSync:
    """UT-013-10: set_detail() 후 스냅샷 파일의 항목 수가 state와 일치해야 한다."""

    def test_snapshot_item_count_matches_state(self, isolated_snapshot):
        """set_detail() 호출 후 파일의 detail_requirements 수가 state와 같아야 한다."""
        state.set_original(_make_originals())
        details = _make_details()
        state.set_detail(details)

        data = json.loads(isolated_snapshot.read_text(encoding="utf-8"))
        assert len(data["detail_requirements"]) == len(state.get_detail())


# ---------------------------------------------------------------------------
# UT-013-11: save_snapshot() — 파일 쓰기 실패 시 예외 억제
# ---------------------------------------------------------------------------


class TestSaveSnapshotSuppressException:
    """UT-013-11: 파일 쓰기 실패 시 예외를 억제하고 호출자에 전파하지 않아야 한다."""

    def test_no_exception_on_write_failure(self, isolated_snapshot):
        """os.replace 실패 시 예외가 호출자에 전파되지 않아야 한다 (SEC-013 예외 억제)."""
        state.set_original(_make_originals())

        # os.replace를 실패하도록 patch
        with patch("os.replace", side_effect=PermissionError("권한 없음")):
            # 예외가 전파되지 않아야 한다
            snapshot.save_snapshot()


# ---------------------------------------------------------------------------
# UT-013-12: DELETE /api/v1/detail/{id} — 존재하는 id로 200 + {"deleted_id": id}
# ---------------------------------------------------------------------------


class TestDeleteEndpointSnapshotIntegration:
    """UT-013-12: 존재하는 id로 DELETE 요청 시 200과 {"deleted_id": id}를 반환해야 한다."""

    def test_returns_200_with_deleted_id(self, isolated_snapshot):
        """존재하는 id로 DELETE 요청 시 200과 deleted_id를 반환해야 한다."""
        # isolated_snapshot fixture가 state를 reset하므로, fixture 이후 state 설정
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
        session = state.get_session()
        with state._lock:
            session.detail_requirements = _make_details()
            session.status = "generated"

        response = client.delete("/api/v1/detail/REQ-001-01")

        assert response.status_code == 200
        assert response.json() == {"deleted_id": "REQ-001-01"}


# ---------------------------------------------------------------------------
# UT-013-13: DELETE /api/v1/detail/{id} — 존재하지 않는 id로 404 + NOT_FOUND
# ---------------------------------------------------------------------------


class TestDeleteEndpointNotFoundIntegration:
    """UT-013-13: 존재하지 않는 id로 DELETE 요청 시 404와 NOT_FOUND 코드를 반환해야 한다."""

    def setup_method(self):
        state.reset_session()

    def test_returns_404_not_found(self):
        """존재하지 않는 id로 DELETE 요청 시 404를 반환해야 한다."""
        response = client.delete("/api/v1/detail/REQ-999-99")

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# UT-013-14: load_snapshot() — 복원 후 state.get_original()이 스냅샷 목록 반환
# ---------------------------------------------------------------------------


class TestLoadSnapshotRestoresOriginals:
    """UT-013-14: 복원 후 state.get_original()이 스냅샷의 original_requirements를 반환해야 한다."""

    def test_original_requirements_restored(self, isolated_snapshot):
        """복원 후 state.get_original()이 스냅샷의 원본 요구사항 목록을 반환해야 한다."""
        originals = _make_originals()
        data = {
            "original_requirements": [o.model_dump() for o in originals],
            "detail_requirements": [d.model_dump() for d in _make_details()],
        }
        isolated_snapshot.write_text(json.dumps(data), encoding="utf-8")

        state.reset_session()
        snapshot.load_snapshot()

        restored = state.get_original()
        assert len(restored) == len(originals)
        assert restored[0].id == "REQ-001"
        assert restored[0].name == "인증"
