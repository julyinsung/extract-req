# REQ-005 설계 — 엑셀 다운로드

> Gate 2a/2b — 담당 범위: REQ-005-01 ~ REQ-005-03

---

## API 엔드포인트

| Method | Path | 설명 | 쿼리 파라미터 | 응답 |
|--------|------|------|------------|------|
| GET | `/api/v1/download` | 엑셀 파일 다운로드 | `session_id`, `stage=1\|2` | `.xlsx` 바이너리 |

응답 헤더:
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="requirements_original_20260401_120000.xlsx"
```

에러:
| HTTP | 코드 | 상황 |
|------|------|------|
| 404 | `SESSION_NOT_FOUND` | 세션 없음 |
| 422 | `DETAIL_NOT_GENERATED` | stage=2 요청인데 상세요구사항 미생성 |

---

## 백엔드 모듈

### `app/services/excel_export_service.py`

```python
class ExcelExportService:
    def export(self, session_id: str, stage: Literal[1, 2]) -> bytes:
        """SessionStore 데이터 → openpyxl → .xlsx 바이너리 반환."""
```

- `stage=1`: `OriginalRequirement[]`만 변환
- `stage=2`: `OriginalRequirement[]` + `DetailRequirement[]` 인터리빙 레이아웃
- `stage=2` 요청 시 detail 미생성이면 `DetailNotGeneratedError` 발생

---

## 엑셀 출력 스펙

### 1단계 엑셀 — 원본 요구사항만

- 파일명: `requirements_original_{YYYYMMDD_HHMMSS}.xlsx`
- 시트명: `원본요구사항`

| 열 | 헤더 | 매핑 필드 |
|----|------|---------|
| A | 요구사항 ID | `OriginalRequirement.id` |
| B | 분류 | `OriginalRequirement.category` |
| C | 요구사항 명칭 | `OriginalRequirement.name` |
| D | 요구사항 내용 | `OriginalRequirement.content` |

```
행 1: 헤더 (굵게, 배경색 #4472C4, 글자색 흰색)
행 2~N: 데이터 (order_index 오름차순)
```

### 2단계 엑셀 — 원본 + 상세 통합

- 파일명: `requirements_full_{YYYYMMDD_HHMMSS}.xlsx`
- 시트명: `상세요구사항`
- 레이아웃: **인터리빙** — 원본 행 직후에 해당 상세 행들 배치

| 열 | 헤더 | 원본 행 | 상세 행 |
|----|------|--------|--------|
| A | 구분 | `원본` | `상세` |
| B | 요구사항 ID | `SFR-001` | `SFR-001-01` |
| C | 상위 요구사항 ID | (빈 셀) | `SFR-001` |
| D | 분류 | 분류명 | 분류명 |
| E | 요구사항 명칭 | 명칭 | 명칭 |
| F | 요구사항 내용 | 내용 | 내용 |

행 배치 예시:
```
행 1: 헤더
행 2: 원본  | SFR-001    |         | 기능 | 지원포털 기능 개선 | ...
행 3: 상세  | SFR-001-01 | SFR-001 | 기능 | 이용자 관리 UI    | ...
행 4: 상세  | SFR-001-02 | SFR-001 | 기능 | 계약 관리 기능    | ...
행 5: 원본  | MHR-001    |         | 유지관리 | 유지관리 인력 | ...
행 6: 상세  | MHR-001-01 | MHR-001 | 유지관리 | PM 역할 정의  | ...
```

행 색상:
```
원본 행:               배경색 #D9E1F2 (연한 파랑)
상세 행:               배경색 흰색
수정된 상세 행(is_modified=True): 배경색 #FFF2CC (연한 노랑)
```

### 공통 포맷 규칙

| 항목 | 규칙 |
|------|------|
| 파일 형식 | `.xlsx` (openpyxl) |
| 헤더 행 고정 | `freeze_panes = "A2"` |
| 열 너비 | A:8, B:15, C:15, D:12, E:30, F:60 (문자 단위) |
| 내용 열 줄바꿈 | `wrap_text=True` |
| 다운로드 방식 | FastAPI `StreamingResponse` |

---

## 프론트엔드 다운로드 처리

```typescript
// src/api/index.ts
function getDownloadUrl(sessionId: string, stage: 1 | 2): string {
  return `/api/v1/download?session_id=${sessionId}&stage=${stage}`
}
```

- `<a href={url} download>` 태그로 GET 요청 — Blob 방식 대비 메모리 부담 없음
- 1단계 버튼: `originalReqs.length > 0` 일 때만 활성화
- 2단계 버튼: `detailReqs.length > 0` 일 때만 활성화

---

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-005-01 | `ExcelExportService.export(stage=1)` | 4컬럼 xlsx, 원본 행 수 일치 |
| UT-005-02 | `ExcelExportService.export(stage=2)` | 6컬럼 xlsx, 원본+상세 인터리빙 순서 확인 |
| UT-005-03 | `GET /api/v1/download` | Content-Type xlsx 헤더 확인 |
| UT-005-04 | 수정 반영 | `is_modified=True` 행 → 2단계 엑셀에 수정값 포함 |
| UT-005-05 | stage=2 미생성 | detailReqs 없을 때 422 반환 |
