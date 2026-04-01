# REQ-001 설계 — HWP 파일 업로드 및 파싱

> Gate 2a — 담당 범위: REQ-001-01 ~ REQ-001-04

---

## API 엔드포인트

| Method | Path | 설명 | 요청 | 응답 |
|--------|------|------|------|------|
| POST | `/api/v1/upload` | HWP 파일 업로드 및 파싱 | `multipart/form-data: file` | `ParseResult` JSON |

### 응답 스키마

```json
{
  "session_id": "uuid-v4-string",
  "requirements": [
    {
      "id": "SFR-001",
      "category": "기능 요구사항",
      "name": "지원포털 기능 개선",
      "content": "o 지원포털 이용자의 관리 기능 개선\n...",
      "order_index": 0
    }
  ]
}
```

### 에러 응답

```json
{ "detail": { "code": "PARSE_ERROR", "message": "HWP 파일을 파싱할 수 없습니다." } }
```

| HTTP | 코드 | 상황 |
|------|------|------|
| 400 | `INVALID_FILE_TYPE` | .hwp 이외 확장자 |
| 400 | `PARSE_ERROR` | 손상된 HWP 파일 |

---

## 백엔드 모듈

### `app/parser/hwp_ole_reader.py` — 재활용 (수정 금지)

```
HWPOLEReader(file_path: str)
  .open() -> bool               # OLE2 매직 바이트 + FileHeader 검증
  .get_bodytext_streams() -> list[str]
  .get_stream_data(stream_name) -> bytes
  .close()
```

- 파일 경로 기반 인터페이스 → 업로드 파일은 반드시 임시 경로에 저장 후 전달

### `app/parser/hwp_body_parser.py` — 재활용 (수정 금지)

```
HwpBodyParser()
  .extract_all(stream_data: bytes) -> List[Dict]
  # 반환: [{"type": "text"|"table", "content"|"data": ...}]
```

- zlib deflate 압축 해제 내부 수행
- 표(table) 인식은 상위 HwpProcessor에서 담당

### `app/parser/hwp_processor.py` — 신규 작성 (어댑터)

```python
class HwpProcessor:
    def process(self, file_path: str) -> list[OriginalRequirement]:
        """HWPOLEReader + HwpBodyParser 조합으로 요구사항 4항목 추출."""
```

- 기존 파서 클래스 자체는 수정하지 않음
- pandas 의존성 없이 순수 Python 객체 반환
- 표(table) 타입 항목에서 열 구조 추론하여 ID/분류/명칭/내용 매핑

### `app/services/hwp_parse_service.py`

```python
class HwpParseService:
    def parse(self, file_bytes: bytes, filename: str) -> ParseResult:
        """임시 저장 → 검증 → 파싱 → 세션 저장 → 임시 파일 삭제."""
```

내부 흐름:
1. `.hwp` 확장자 검사 (fail-fast)
2. `tempfile.NamedTemporaryFile`로 임시 저장
3. `olefile.isOleFile()` 검사
4. `HwpProcessor.process()` 호출
5. `state.reset_session()` + `session.set_original(reqs)` 저장
6. 임시 파일 삭제 (성공/실패 모두 `finally` 블록에서)

---

## 데이터 모델

```python
# app/models/requirement.py

class OriginalRequirement(BaseModel):
    id: str           # HWP 원문 ID 그대로 (예: "SFR-001")
    category: str     # 요구사항 분류
    name: str         # 요구사항 명칭
    content: str      # 요구사항 내용
    order_index: int  # 출력 순서 (0-based)

class ParseResult(BaseModel):
    session_id: str
    requirements: list[OriginalRequirement]
```

---

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-001-01 | `HwpProcessor.process()` | 정상 HWP → OriginalRequirement 리스트 반환, 4개 필드 모두 비어있지 않음 |
| UT-001-02 | `HwpProcessor.process()` | 비 HWP 파일 경로 → ValueError 발생 |
| UT-001-03 | `HwpParseService.parse()` | 정상 바이트 → ParseResult 반환, session_id 포함 |
| UT-001-04 | `HwpParseService.parse()` | .docx 파일 → `INVALID_FILE_TYPE` 예외 |
| UT-001-05 | 임시 파일 삭제 | 파싱 완료/실패 후 tmp 파일 미존재 확인 |

---

## SEC-ID

| SEC-ID | 내용 |
|--------|------|
| SEC-001-01 | 파일 확장자(.hwp) + MIME 타입 + OLE2 시그니처 3중 검증 |
| SEC-001-02 | 업로드 파일 크기 제한 50MB (FastAPI `UploadFile` 처리 전 검사) |
| SEC-001-03 | 임시 파일 경로 고정 (`tempfile` 사용, Path Traversal 방지) |
