"""HWP 파일 업로드 및 파싱 서비스.

SEC-001-01: 확장자 + MIME 타입 + OLE2 시그니처 3중 검증 수행.
SEC-001-02: 파일 크기 50MB 상한 적용.
SEC-001-03: tempfile로 임시 경로 생성 — Path Traversal 방지.
파싱 성공/실패 무관하게 finally 블록에서 임시 파일을 삭제한다.
"""

import os
import tempfile

import olefile
from fastapi import HTTPException, UploadFile

import app.state as state
from app.models.api import ParseResponse
from app.parser.hwp_processor import HwpProcessor

# SEC-001-02: 업로드 파일 크기 상한 (50 MiB)
_MAX_FILE_SIZE = 50 * 1024 * 1024

# SEC-001-03: 임시 파일 저장 디렉토리 (고정 경로 — 경로 조작 방지)
_TMP_DIR = "data/tmp"

# SEC-001-01: HWP 파일로 허용하는 MIME 타입 목록
# application/octet-stream은 브라우저/OS 종류에 따라 HWP에 매핑되는 범용 타입이므로 포함
_ALLOWED_MIME_TYPES = frozenset(
    {
        "application/x-hwp",
        "application/haansofthwp",
        "application/vnd.hancom.hwp",
        "application/octet-stream",
    }
)


class HwpParseService:
    """HWP 업로드 파일을 검증하고 파싱하여 세션에 저장하는 서비스."""

    async def parse(self, file: UploadFile) -> ParseResponse:
        """업로드된 HWP 파일을 파싱하고 ParseResponse를 반환한다.

        Args:
            file: FastAPI UploadFile 객체

        Returns:
            session_id와 파싱된 요구사항 목록을 담은 ParseResponse

        Raises:
            HTTPException 400 INVALID_FILE_TYPE: .hwp 이외 확장자 또는 허용되지 않은 MIME 타입
            HTTPException 400 FILE_TOO_LARGE: 50MB 초과
            HTTPException 400 PARSE_ERROR: OLE2 검증 실패 또는 파싱 오류
        """
        self._validate_extension(file.filename)
        self._validate_mime_type(file.content_type)

        contents = await file.read()
        self._validate_size(contents)

        tmp_path = None
        try:
            tmp_path = self._save_tmp(contents)
            self._validate_ole_signature(tmp_path)

            processor = HwpProcessor()
            reqs = processor.process(tmp_path)

            # 새 업로드이므로 이전 세션 데이터를 전부 폐기하고 새 세션 생성
            session = state.reset_session()
            state.set_original(reqs)

            return ParseResponse(session_id=session.session_id, requirements=reqs)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={"code": "PARSE_ERROR", "message": f"파일을 파싱할 수 없습니다: {str(e)}"},
            )
        finally:
            # 성공·실패 무관하게 임시 파일 삭제 (SEC-001-03)
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    # ------------------------------------------------------------------
    # 내부 검증 메서드
    # ------------------------------------------------------------------

    def _validate_extension(self, filename: str) -> None:
        """SEC-001-01 (1/3): 파일 확장자가 .hwp인지 검사한다."""
        if not filename or not filename.lower().endswith(".hwp"):
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_FILE_TYPE", "message": "HWP 파일만 업로드 가능합니다."},
            )

    def _validate_mime_type(self, content_type: str | None) -> None:
        """SEC-001-01 (2/3): multipart Content-Type 헤더로 MIME 타입을 검사한다.

        허용 목록(_ALLOWED_MIME_TYPES)에 없는 MIME 타입은 거부한다.
        content_type이 None이면 브라우저가 헤더를 전송하지 않은 경우로 간주하여
        허용하지 않는다.
        """
        if not content_type or content_type.split(";")[0].strip() not in _ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_FILE_TYPE", "message": "허용되지 않는 파일 형식입니다."},
            )

    def _validate_size(self, contents: bytes) -> None:
        """SEC-001-02: 파일 크기가 50MB 이하인지 검사한다."""
        if len(contents) > _MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail={"code": "FILE_TOO_LARGE", "message": "파일 크기는 50MB 이하여야 합니다."},
            )

    def _save_tmp(self, contents: bytes) -> str:
        """SEC-001-03: 고정 디렉토리에 임시 파일을 생성하고 경로를 반환한다.

        tempfile.NamedTemporaryFile로 생성하여 OS가 유일한 경로를 보장한다.
        """
        os.makedirs(_TMP_DIR, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".hwp", delete=False, dir=_TMP_DIR) as f:
            f.write(contents)
            return f.name

    def _validate_ole_signature(self, tmp_path: str) -> None:
        """SEC-001-01 (3/3): OLE2 매직 바이트로 HWP 파일임을 검증한다."""
        if not olefile.isOleFile(tmp_path):
            raise HTTPException(
                status_code=400,
                detail={"code": "PARSE_ERROR", "message": "유효한 HWP 파일이 아닙니다."},
            )
