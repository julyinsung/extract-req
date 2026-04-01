# REQ-001 설계 — HWP 파일 업로드 및 파싱

> 통합 설계 문서 참조: `req-all-design.md`

## 담당 범위

REQ-001-01 ~ REQ-001-04: HWP 파일 업로드, 파싱, 오류 처리

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/upload` | HWP 파일 업로드 및 파싱 |

## 서비스 모듈

- `HwpParseService` — HWPOLEReader + HwpBodyParser + HwpProcessor 조합
- `SessionStore.save_original(session_id, reqs)` — 파싱 결과 인메모리 저장
- 임시 파일: `data/tmp/` 하위 저장, 파싱 완료 후 즉시 삭제 (REQ-006-03)

## 재활용 파서

```
HWPOLEReader → get_bodytext_streams()
HwpBodyParser → extract_all(stream_data)
HwpProcessor → process_file() → OriginalRequirement 리스트 반환
```

추출 필드: `id`, `category`(분류), `name`(명칭), `content`(내용)

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-001-01 | `HwpParseService.parse()` | 정상 HWP → OriginalRequirement 리스트 반환 |
| UT-001-02 | `HwpParseService.parse()` | 비 HWP 파일 → ValueError 발생 |
| UT-001-03 | `POST /api/v1/upload` | 정상 업로드 → 200 + 파싱 결과 반환 |
| UT-001-04 | `POST /api/v1/upload` | 지원 안 되는 확장자 → 400 오류 반환 |
| UT-001-05 | 임시 파일 삭제 | 파싱 완료/실패 후 tmp 파일 미존재 확인 |

## SEC-ID

| SEC-ID | 내용 |
|--------|------|
| SEC-001-01 | 업로드 파일 확장자 및 MIME 타입 이중 검증 (.hwp만 허용) |
| SEC-001-02 | 업로드 파일 크기 제한 (50MB 이하) |
| SEC-001-03 | 임시 파일 경로 고정 (Path Traversal 방지) |
