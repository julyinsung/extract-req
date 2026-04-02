"""인메모리 세션 싱글턴 관리 모듈.

단일 사용자 전제(REQ-006-04)로 프로세스 전역에 단 하나의 SessionState를 유지한다.
멀티스레드 환경에서의 경쟁 조건을 방지하기 위해 threading.Lock을 사용한다.
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
    """AI 생성 상세요구사항 저장 및 세션 상태를 'generated'로 전이한다."""
    session = get_session()
    with _lock:
        session.detail_requirements = reqs
        session.status = "generated"


def get_detail() -> list[DetailRequirement]:
    """저장된 상세요구사항 목록을 반환한다."""
    return get_session().detail_requirements


def get_sdk_session_id() -> str | None:
    """저장된 claude-agent-sdk session_id를 반환한다. 없으면 None."""
    return get_session().sdk_session_id


def set_sdk_session_id(session_id: str) -> None:
    """claude-agent-sdk ResultMessage에서 추출한 session_id를 저장한다.

    SEC-009-03: 기존 _lock 패턴과 동일하게 스레드 안전성을 보장한다.
    """
    session = get_session()
    with _lock:
        session.sdk_session_id = session_id


def patch_detail(req_id: str, field: str, value: str) -> bool:
    """특정 상세요구사항의 단일 필드를 수정하고 is_modified를 True로 표시한다.

    Args:
        req_id: 수정할 DetailRequirement의 id
        field: 수정할 필드명 ('name', 'content', 'category' 중 하나)
        value: 새 값

    Returns:
        수정 성공 시 True, 해당 id가 없으면 False
    """
    session = get_session()
    with _lock:
        for req in session.detail_requirements:
            if req.id == req_id:
                setattr(req, field, value)
                req.is_modified = True
                return True
    return False
