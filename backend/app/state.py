"""인메모리 세션 싱글턴 관리 모듈.

단일 사용자 전제(REQ-006-04)로 프로세스 전역에 단 하나의 SessionState를 유지한다.
멀티스레드 환경에서의 경쟁 조건을 방지하기 위해 threading.Lock을 사용한다.
변경 유발 지점(set_detail, patch_detail, delete_detail)에서 snapshot.save_snapshot()을
_lock 블록 외부에서 호출하여 스냅샷 동기화 및 데드락 방지를 보장한다 (REQ-013).
"""

import threading

from app.models.session import SessionState
from app.models.requirement import OriginalRequirement, DetailRequirement


_session: SessionState | None = None
_lock = threading.Lock()


def get_session() -> SessionState:
    """현재 세션을 반환한다. 세션이 없으면 새로 생성한다."""
    global _session
    with _lock:
        if _session is None:
            _session = SessionState()
        return _session


def reset_session() -> SessionState:
    """새 HWP 업로드 시 호출. 이전 세션 데이터 전체 폐기 후 새 세션 반환."""
    global _session
    with _lock:
        _session = SessionState()
        return _session


def set_original(reqs: list[OriginalRequirement]) -> None:
    """원본 요구사항 저장 및 세션 상태를 'parsed'로 전이한다."""
    session = get_session()
    with _lock:
        session.original_requirements = reqs
        session.status = "parsed"


def get_original() -> list[OriginalRequirement]:
    """저장된 원본 요구사항 목록을 반환한다."""
    return get_session().original_requirements


def set_detail(reqs: list[DetailRequirement]) -> None:
    """AI 생성 상세요구사항 저장 및 세션 상태를 'generated'로 전이한다.

    REQ-013: _lock 블록 해제 후 snapshot.save_snapshot()을 호출하여 영속화한다.
    데드락 방지를 위해 _lock 블록 외부에서 호출한다.
    """
    session = get_session()
    with _lock:
        session.detail_requirements = reqs
        session.status = "generated"

    # REQ-013: _lock 블록 외부에서 호출 — 데드락 방지
    import app.snapshot as snapshot
    snapshot.save_snapshot()


def get_detail() -> list[DetailRequirement]:
    """저장된 상세요구사항 목록을 반환한다."""
    return get_session().detail_requirements


def get_sdk_session_id(req_group: str) -> str | None:
    """지정한 REQ 그룹의 claude-agent-sdk session_id를 반환한다. 없으면 None.

    Args:
        req_group: REQ 그룹 ID (예: "REQ-001")

    Returns:
        해당 그룹의 SDK session_id, 없으면 None
    """
    return get_session().sdk_sessions.get(req_group)


def set_sdk_session_id(req_group: str, session_id: str) -> None:
    """claude-agent-sdk ResultMessage에서 추출한 session_id를 REQ 그룹 키로 저장한다.

    Args:
        req_group: REQ 그룹 ID (예: "REQ-001")
        session_id: SDK ResultMessage에서 추출한 session_id

    SEC-009-03: 기존 _lock 패턴과 동일하게 스레드 안전성을 보장한다.
    REQ-009-04: 그룹별 독립 세션 관리로 다른 그룹의 session_id에 영향 없음.
    """
    session = get_session()
    with _lock:
        session.sdk_sessions[req_group] = session_id


def get_original_by_group(req_group: str) -> OriginalRequirement | None:
    """지정한 REQ 그룹에 해당하는 원본 요구사항 1건을 반환한다.

    Args:
        req_group: REQ 그룹 ID (예: "REQ-001")

    Returns:
        해당 id의 OriginalRequirement, 없으면 None
    """
    for req in get_session().original_requirements:
        if req.id == req_group:
            return req
    return None


def get_detail_by_group(req_group: str) -> list[DetailRequirement]:
    """지정한 REQ 그룹에 속하는 상세요구사항 목록을 반환한다.

    Args:
        req_group: REQ 그룹 ID (예: "REQ-001")

    Returns:
        parent_id == req_group인 DetailRequirement 목록
    """
    return [r for r in get_session().detail_requirements if r.parent_id == req_group]


def replace_detail_group(req_group: str, items: list[DetailRequirement]) -> None:
    """지정한 REQ 그룹의 상세요구사항 전체를 items로 교체한다.

    교체된 모든 항목의 is_modified를 True로 설정한다.
    다른 그룹의 상세항목은 변경되지 않는다.

    Args:
        req_group: 교체 대상 REQ 그룹 ID
        items: 새로 설정할 DetailRequirement 목록

    REQ-013: 교체 성공 후 _lock 블록 외부에서 snapshot.save_snapshot()을 호출한다.
    """
    session = get_session()
    with _lock:
        # 다른 그룹의 항목은 유지하고, 해당 그룹 항목만 교체한다
        other_groups = [r for r in session.detail_requirements if r.parent_id != req_group]
        for item in items:
            item.is_modified = True
        session.detail_requirements = other_groups + items

    # REQ-013: _lock 블록 외부에서 호출 — 데드락 방지
    import app.snapshot as snapshot
    snapshot.save_snapshot()


def patch_detail(req_id: str, field: str, value: str) -> bool:
    """특정 상세요구사항의 단일 필드를 수정하고 is_modified를 True로 표시한다.

    Args:
        req_id: 수정할 DetailRequirement의 id
        field: 수정할 필드명 ('name', 'content', 'category' 중 하나)
        value: 새 값

    Returns:
        수정 성공 시 True, 해당 id가 없으면 False

    REQ-013: 수정 성공 시에만 _lock 블록 외부에서 snapshot.save_snapshot()을 호출한다.
    """
    session = get_session()
    modified = False
    with _lock:
        for req in session.detail_requirements:
            if req.id == req_id:
                setattr(req, field, value)
                req.is_modified = True
                modified = True
                break

    if modified:
        # REQ-013: 수정 성공 시에만 스냅샷 저장 — _lock 블록 외부에서 호출
        import app.snapshot as snapshot
        snapshot.save_snapshot()

    return modified


def delete_detail(req_id: str) -> bool:
    """특정 id의 상세요구사항을 인메모리 state에서 제거한다 (REQ-012/REQ-013).

    Args:
        req_id: 삭제할 DetailRequirement의 id

    Returns:
        삭제 성공 시 True, 해당 id가 없으면 False

    SEC-012-02: id는 문자열 동등 비교만 사용하므로 경로 순회 위협 없음.
    REQ-013: 삭제 성공 시 _lock 블록 외부에서 snapshot.save_snapshot()을 호출한다.
    """
    session = get_session()
    deleted = False
    with _lock:
        original_count = len(session.detail_requirements)
        session.detail_requirements = [
            r for r in session.detail_requirements if r.id != req_id
        ]
        deleted = len(session.detail_requirements) < original_count

    if deleted:
        # REQ-013: 삭제 성공 시에만 스냅샷 저장 — _lock 블록 외부에서 호출
        import app.snapshot as snapshot
        snapshot.save_snapshot()

    return deleted
