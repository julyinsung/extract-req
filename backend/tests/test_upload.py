"""HWP 업로드 및 파싱 단위/통합 테스트.

UT-001-01: HwpProcessor.process() — 정상 HWP → OriginalRequirement 리스트 반환
UT-001-02: HwpProcessor.process() — 비 HWP 파일 경로 → ValueError 발생
UT-001-03: HwpParseService.parse() — 정상 바이트 → ParseResponse(session_id 포함) 반환
UT-001-04: HwpParseService.parse() — .docx 파일 → INVALID_FILE_TYPE 예외
UT-001-05: 임시 파일 삭제 — 파싱 완료/실패 후 tmp 파일 미존재 확인
"""

import os
import struct
import tempfile
import zlib
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

import app.state as state


# ---------------------------------------------------------------------------
# 테스트용 HWP 바이트 픽스처
# ---------------------------------------------------------------------------

def _make_minimal_ole_hwp() -> bytes:
    """OLE2 매직 바이트를 가진 최소 HWP 바이너리를 생성한다.

    실제 파일 없이 olefile.isOleFile() 검증을 통과할 수 있도록
    OLE 컴파운드 문서의 매직 바이트(D0 CF 11 E0 A1 B1 1A E1)를 포함한다.
    """
    # OLE2 시그니처 8바이트 + 나머지를 0으로 채워 512바이트(최소 섹터 크기) 구성
    magic = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
    return magic + b'\x00' * (512 - len(magic))


def _make_fake_requirements() -> list:
    """테스트용 OriginalRequirement 목록을 생성한다."""
    from app.models.requirement import OriginalRequirement

    return [
        OriginalRequirement(
            id="SFR-001",
            category="기능 요구사항",
            name="지원포털 기능 개선",
            content="o 지원포털 이용자의 관리 기능 개선",
            order_index=0,
        )
    ]


# ---------------------------------------------------------------------------
# UT-001-01: HwpProcessor.process() 정상 경로
# ---------------------------------------------------------------------------

class TestHwpProcessorProcess:
    """UT-001-01: HwpProcessor.process() 정상 HWP → OriginalRequirement 반환."""

    def test_process_returns_original_requirement_list(self, tmp_path):
        """HwpProcessor.process()가 OriginalRequirement 리스트를 반환해야 한다.

        실제 HWP 파일이 없으므로 HWPOLEReader와 HwpBodyParser를 mock 처리한다.
        """
        from app.models.requirement import OriginalRequirement
        from app.parser.hwp_processor import HwpProcessor

        fake_reqs = _make_fake_requirements()

        with patch("app.parser.hwp_processor.HWPOLEReader") as MockReader, \
             patch("app.parser.hwp_processor.HwpBodyParser") as MockParser:

            # HWPOLEReader 컨텍스트 매니저 설정
            mock_reader_instance = MagicMock()
            mock_reader_instance.get_bodytext_streams.return_value = ["BodyText/Section0"]
            mock_reader_instance.get_stream_data.return_value = b"\x00"
            MockReader.return_value.__enter__ = MagicMock(return_value=mock_reader_instance)
            MockReader.return_value.__exit__ = MagicMock(return_value=False)

            # HwpBodyParser.extract_all 설정
            mock_parser_instance = MagicMock()
            mock_parser_instance.extract_all.return_value = [
                {
                    "type": "table",
                    "data": {
                        "cells": [
                            "요구사항 고유번호", "SFR-001",
                            "요구사항 명칭", "지원포털 기능 개선",
                            "요구사항 분류", "기능 요구사항",
                            "세부내용", "o 지원포털 이용자의 관리 기능 개선",
                        ],
                        "rows": 4,
                        "cols": 2,
                    },
                }
            ]
            MockParser.return_value = mock_parser_instance

            # 실제 파일 경로는 mock이 가로채므로 존재하지 않아도 무방
            dummy_path = str(tmp_path / "dummy.hwp")
            processor = HwpProcessor()
            result = processor.process(dummy_path)

        assert isinstance(result, list)
        assert len(result) == 1
        req = result[0]
        assert isinstance(req, OriginalRequirement)
        # UT-001-01: 4개 필드 모두 비어있지 않음
        assert req.id
        assert req.category
        assert req.name
        assert req.content


# ---------------------------------------------------------------------------
# UT-001-02: HwpProcessor.process() 비 HWP 파일 → ValueError
# ---------------------------------------------------------------------------

class TestHwpProcessorInvalidFile:
    """UT-001-02: HwpProcessor.process() 비 HWP 파일 경로 → ValueError 발생."""

    def test_process_raises_value_error_for_non_hwp(self, tmp_path):
        """OLE2 시그니처가 없는 파일을 전달하면 ValueError가 발생해야 한다."""
        from app.parser.hwp_processor import HwpProcessor

        # 일반 텍스트를 .hwp 확장자로 저장하여 비 HWP 파일 시뮬레이션
        fake_hwp = tmp_path / "not_real.hwp"
        fake_hwp.write_bytes(b"this is not an OLE file")

        processor = HwpProcessor()
        with pytest.raises((ValueError, Exception)):
            processor.process(str(fake_hwp))


# ---------------------------------------------------------------------------
# UT-001-03: HwpParseService.parse() 정상 경로
# ---------------------------------------------------------------------------

class TestHwpParseServiceParse:
    """UT-001-03: HwpParseService.parse() 정상 바이트 → ParseResponse 반환."""

    @pytest.mark.asyncio
    async def test_parse_returns_parse_response_with_session_id(self, tmp_path):
        """정상 HWP 바이트를 전달하면 session_id가 포함된 ParseResponse를 반환해야 한다."""
        from app.models.api import ParseResponse
        from app.services.hwp_parse_service import HwpParseService

        state.reset_session()

        fake_reqs = _make_fake_requirements()
        fake_bytes = _make_minimal_ole_hwp()

        upload_file = MagicMock()
        upload_file.filename = "sample.hwp"
        upload_file.content_type = "application/octet-stream"
        upload_file.read = MagicMock(return_value=fake_bytes)

        # async read를 처리하기 위해 코루틴으로 wrapping
        async def async_read():
            return fake_bytes

        upload_file.read = async_read

        with patch("app.services.hwp_parse_service.olefile.isOleFile", return_value=True), \
             patch("app.services.hwp_parse_service.HwpProcessor") as MockProcessor:

            mock_proc = MagicMock()
            mock_proc.process.return_value = fake_reqs
            MockProcessor.return_value = mock_proc

            service = HwpParseService()
            result = await service.parse(upload_file)

        assert isinstance(result, ParseResponse)
        assert result.session_id
        assert len(result.session_id) > 0
        assert len(result.requirements) == 1


# ---------------------------------------------------------------------------
# UT-001-04: HwpParseService.parse() .docx → INVALID_FILE_TYPE
# ---------------------------------------------------------------------------

class TestHwpParseServiceInvalidType:
    """UT-001-04: .docx 파일 업로드 → INVALID_FILE_TYPE 예외."""

    @pytest.mark.asyncio
    async def test_parse_raises_for_docx_extension(self):
        """확장자가 .docx인 파일을 전달하면 INVALID_FILE_TYPE HTTPException이 발생해야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        upload_file = MagicMock()
        upload_file.filename = "document.docx"

        service = HwpParseService()
        with pytest.raises(HTTPException) as exc_info:
            await service.parse(upload_file)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "INVALID_FILE_TYPE"

    @pytest.mark.asyncio
    async def test_parse_raises_for_no_extension(self):
        """확장자가 없는 파일을 전달하면 INVALID_FILE_TYPE HTTPException이 발생해야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        upload_file = MagicMock()
        upload_file.filename = "noextension"

        service = HwpParseService()
        with pytest.raises(HTTPException) as exc_info:
            await service.parse(upload_file)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "INVALID_FILE_TYPE"

    @pytest.mark.asyncio
    async def test_parse_raises_for_oversized_file(self):
        """50MB를 초과하는 파일을 전달하면 FILE_TOO_LARGE HTTPException이 발생해야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        upload_file = MagicMock()
        upload_file.filename = "big.hwp"
        upload_file.content_type = "application/octet-stream"

        oversized = b"\x00" * (50 * 1024 * 1024 + 1)

        async def async_read():
            return oversized

        upload_file.read = async_read

        service = HwpParseService()
        with pytest.raises(HTTPException) as exc_info:
            await service.parse(upload_file)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "FILE_TOO_LARGE"


# ---------------------------------------------------------------------------
# UT-001-05: 임시 파일 삭제 확인
# ---------------------------------------------------------------------------

class TestTmpFileDeletion:
    """UT-001-05: 파싱 완료/실패 후 tmp 파일이 남아있지 않아야 한다."""

    @pytest.mark.asyncio
    async def test_tmp_file_deleted_on_success(self):
        """파싱 성공 후 임시 파일이 삭제되어야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        state.reset_session()
        fake_reqs = _make_fake_requirements()
        fake_bytes = _make_minimal_ole_hwp()

        captured_path: list[str] = []

        original_save = HwpParseService._save_tmp

        def spy_save(self_inner, contents):
            path = original_save(self_inner, contents)
            captured_path.append(path)
            return path

        upload_file = MagicMock()
        upload_file.filename = "test.hwp"
        upload_file.content_type = "application/octet-stream"

        async def async_read():
            return fake_bytes

        upload_file.read = async_read

        with patch.object(HwpParseService, "_save_tmp", spy_save), \
             patch("app.services.hwp_parse_service.olefile.isOleFile", return_value=True), \
             patch("app.services.hwp_parse_service.HwpProcessor") as MockProcessor:

            mock_proc = MagicMock()
            mock_proc.process.return_value = fake_reqs
            MockProcessor.return_value = mock_proc

            service = HwpParseService()
            await service.parse(upload_file)

        assert len(captured_path) == 1
        # 파싱 성공 후 파일이 존재하지 않아야 함
        assert not os.path.exists(captured_path[0])

    @pytest.mark.asyncio
    async def test_tmp_file_deleted_on_parse_failure(self):
        """파싱 실패(예외 발생) 후에도 임시 파일이 삭제되어야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        fake_bytes = _make_minimal_ole_hwp()
        captured_path: list[str] = []

        original_save = HwpParseService._save_tmp

        def spy_save(self_inner, contents):
            path = original_save(self_inner, contents)
            captured_path.append(path)
            return path

        upload_file = MagicMock()
        upload_file.filename = "error.hwp"
        upload_file.content_type = "application/octet-stream"

        async def async_read():
            return fake_bytes

        upload_file.read = async_read

        with patch.object(HwpParseService, "_save_tmp", spy_save), \
             patch("app.services.hwp_parse_service.olefile.isOleFile", return_value=True), \
             patch("app.services.hwp_parse_service.HwpProcessor") as MockProcessor:

            mock_proc = MagicMock()
            mock_proc.process.side_effect = RuntimeError("파싱 실패 시뮬레이션")
            MockProcessor.return_value = mock_proc

            service = HwpParseService()
            with pytest.raises(HTTPException):
                await service.parse(upload_file)

        assert len(captured_path) == 1
        # 파싱 실패 후에도 파일이 존재하지 않아야 함
        assert not os.path.exists(captured_path[0])


# ---------------------------------------------------------------------------
# POST /api/v1/upload 통합 테스트
# ---------------------------------------------------------------------------

class TestUploadEndpoint:
    """POST /api/v1/upload 엔드포인트 통합 테스트."""

    @pytest.mark.asyncio
    async def test_upload_endpoint_returns_parse_response(self):
        """정상 HWP 파일 업로드 시 200과 ParseResponse JSON을 반환해야 한다."""
        from app.main import app

        state.reset_session()
        fake_reqs = _make_fake_requirements()

        with patch("app.services.hwp_parse_service.olefile.isOleFile", return_value=True), \
             patch("app.services.hwp_parse_service.HwpProcessor") as MockProcessor:

            mock_proc = MagicMock()
            mock_proc.process.return_value = fake_reqs
            MockProcessor.return_value = mock_proc

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/upload",
                    files={"file": ("sample.hwp", _make_minimal_ole_hwp(), "application/octet-stream")},
                )

        assert response.status_code == 200
        body = response.json()
        assert "session_id" in body
        assert "requirements" in body
        assert len(body["requirements"]) == 1

    @pytest.mark.asyncio
    async def test_upload_endpoint_rejects_docx(self):
        """docx 파일 업로드 시 400 INVALID_FILE_TYPE을 반환해야 한다."""
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/upload",
                files={"file": ("document.docx", b"fake content", "application/octet-stream")},
            )

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["code"] == "INVALID_FILE_TYPE"


# ---------------------------------------------------------------------------
# SEC-001-01 MIME 타입 검증 단위 테스트
# ---------------------------------------------------------------------------

class TestHwpParseServiceMimeValidation:
    """SEC-001-01 (2/3): _validate_mime_type() — MIME 타입 검증."""

    @pytest.mark.asyncio
    async def test_parse_allows_application_x_hwp(self):
        """content_type=application/x-hwp 이면 파싱이 진행되어야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        state.reset_session()
        fake_reqs = _make_fake_requirements()
        fake_bytes = _make_minimal_ole_hwp()

        upload_file = MagicMock()
        upload_file.filename = "sample.hwp"
        upload_file.content_type = "application/x-hwp"

        async def async_read():
            return fake_bytes

        upload_file.read = async_read

        with patch("app.services.hwp_parse_service.olefile.isOleFile", return_value=True), \
             patch("app.services.hwp_parse_service.HwpProcessor") as MockProcessor:

            mock_proc = MagicMock()
            mock_proc.process.return_value = fake_reqs
            MockProcessor.return_value = mock_proc

            service = HwpParseService()
            result = await service.parse(upload_file)

        from app.models.api import ParseResponse
        assert isinstance(result, ParseResponse)

    @pytest.mark.asyncio
    async def test_parse_allows_application_haansofthwp(self):
        """content_type=application/haansofthwp 이면 파싱이 진행되어야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        state.reset_session()
        fake_reqs = _make_fake_requirements()
        fake_bytes = _make_minimal_ole_hwp()

        upload_file = MagicMock()
        upload_file.filename = "sample.hwp"
        upload_file.content_type = "application/haansofthwp"

        async def async_read():
            return fake_bytes

        upload_file.read = async_read

        with patch("app.services.hwp_parse_service.olefile.isOleFile", return_value=True), \
             patch("app.services.hwp_parse_service.HwpProcessor") as MockProcessor:

            mock_proc = MagicMock()
            mock_proc.process.return_value = fake_reqs
            MockProcessor.return_value = mock_proc

            service = HwpParseService()
            result = await service.parse(upload_file)

        from app.models.api import ParseResponse
        assert isinstance(result, ParseResponse)

    @pytest.mark.asyncio
    async def test_parse_allows_octet_stream(self):
        """content_type=application/octet-stream 이면 파싱이 진행되어야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        state.reset_session()
        fake_reqs = _make_fake_requirements()
        fake_bytes = _make_minimal_ole_hwp()

        upload_file = MagicMock()
        upload_file.filename = "sample.hwp"
        upload_file.content_type = "application/octet-stream"

        async def async_read():
            return fake_bytes

        upload_file.read = async_read

        with patch("app.services.hwp_parse_service.olefile.isOleFile", return_value=True), \
             patch("app.services.hwp_parse_service.HwpProcessor") as MockProcessor:

            mock_proc = MagicMock()
            mock_proc.process.return_value = fake_reqs
            MockProcessor.return_value = mock_proc

            service = HwpParseService()
            result = await service.parse(upload_file)

        from app.models.api import ParseResponse
        assert isinstance(result, ParseResponse)

    @pytest.mark.asyncio
    async def test_parse_rejects_text_plain_mime(self):
        """content_type=text/plain 이면 INVALID_FILE_TYPE 예외가 발생해야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        upload_file = MagicMock()
        upload_file.filename = "sample.hwp"
        upload_file.content_type = "text/plain"

        service = HwpParseService()
        with pytest.raises(HTTPException) as exc_info:
            await service.parse(upload_file)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "INVALID_FILE_TYPE"

    @pytest.mark.asyncio
    async def test_parse_rejects_none_content_type(self):
        """content_type=None 이면 INVALID_FILE_TYPE 예외가 발생해야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        upload_file = MagicMock()
        upload_file.filename = "sample.hwp"
        upload_file.content_type = None

        service = HwpParseService()
        with pytest.raises(HTTPException) as exc_info:
            await service.parse(upload_file)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "INVALID_FILE_TYPE"

    @pytest.mark.asyncio
    async def test_parse_rejects_image_jpeg_mime(self):
        """content_type=image/jpeg 이면 INVALID_FILE_TYPE 예외가 발생해야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        upload_file = MagicMock()
        upload_file.filename = "sample.hwp"
        upload_file.content_type = "image/jpeg"

        service = HwpParseService()
        with pytest.raises(HTTPException) as exc_info:
            await service.parse(upload_file)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "INVALID_FILE_TYPE"

    def test_validate_mime_type_with_charset_param(self):
        """content_type에 charset 파라미터가 붙어도 기본 타입이 허용되면 통과해야 한다."""
        from app.services.hwp_parse_service import HwpParseService

        service = HwpParseService()
        # 예외가 발생하지 않아야 한다
        service._validate_mime_type("application/octet-stream; charset=utf-8")
