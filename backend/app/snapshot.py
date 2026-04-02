"""스냅샷 저장/복원 전담 모듈 (REQ-013).

변경 유발 지점(set_detail, patch_detail, delete_detail)에서 호출되어
session_snapshot.json을 최신 1개로 유지한다.
서버 기동 시 load_snapshot()으로 인메모리 state를 복원한다.

SEC-013-01: SNAPSHOT_PATH는 모듈 내부 상수로 고정. 외부 입력으로 변경 불가.
SEC-013-02: load_snapshot() 시 Pydantic 모델로 역직렬화하여 스키마 검증 수행.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# SEC-013-01: 경로를 상수로 고정하여 외부 입력으로 경로 변경 불가
SNAPSHOT_PATH = Path(__file__).parent.parent.parent / "backend" / "data" / "session_snapshot.json"
_TMP_PATH = SNAPSHOT_PATH.with_suffix(".tmp")


def save_snapshot() -> None:
    """현재 state를 JSON으로 직렬화하여 SNAPSHOT_PATH에 원자적으로 저장한다.

    실패 시 예외를 억제하고 로그만 출력한다.
    스냅샷 저장 실패가 API 응답을 막아서는 안 된다.

    저장 대상: original_requirements, detail_requirements만 저장.
    session_id, chat_messages, sdk_session_id는 제외한다.
    """
    try:
        # snapshot.py → state.py 순환 import 방지를 위해 함수 내에서 import
        import app.state as state

        session = state.get_session()
        data = {
            "original_requirements": [
                r.model_dump() for r in session.original_requirements
            ],
            "detail_requirements": [
                r.model_dump() for r in session.detail_requirements
            ],
        }

        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # 원자적 쓰기: tmp 파일에 쓴 후 os.replace()로 교체
        _TMP_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(str(_TMP_PATH), str(SNAPSHOT_PATH))

        logger.debug("스냅샷 저장 완료: %s", SNAPSHOT_PATH)
    except Exception as exc:  # noqa: BLE001
        logger.error("스냅샷 저장 실패 (억제): %s", exc)


def load_snapshot() -> bool:
    """SNAPSHOT_PATH 파일을 읽어 state를 복원한다.

    복원 성공 시 True, 파일 없거나 파싱 실패 시 False.
    파싱 실패 시 예외를 억제하여 서버 기동을 중단하지 않는다.

    SEC-013-02: Pydantic 모델로 역직렬화하여 스키마 검증 수행.
    파싱 실패 시 전체 복원을 취소하고 빈 state로 기동한다.

    Returns:
        True: 복원 성공, False: 파일 없음 또는 파싱 실패
    """
    if not SNAPSHOT_PATH.exists():
        logger.info("스냅샷 파일 없음. 빈 state로 기동: %s", SNAPSHOT_PATH)
        return False

    try:
        # snapshot.py → state.py 순환 import 방지를 위해 함수 내에서 import
        import app.state as state
        from app.models.requirement import OriginalRequirement, DetailRequirement

        raw = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

        # SEC-013-02: Pydantic 모델로 역직렬화 — 스키마 검증
        originals = [OriginalRequirement(**item) for item in raw.get("original_requirements", [])]
        details = [DetailRequirement(**item) for item in raw.get("detail_requirements", [])]

        state.set_original(originals)
        # set_detail 내부에서 save_snapshot()이 다시 호출되나,
        # 복원 직후 동일 데이터로 덮어쓰기이므로 무한 루프 아님 (설계 문서 허용).
        state.set_detail(details)

        logger.info(
            "스냅샷 복원 성공: 원본 %d건, 상세 %d건",
            len(originals),
            len(details),
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("스냅샷 복원 실패 (억제). 빈 state로 기동: %s", exc)
        return False
