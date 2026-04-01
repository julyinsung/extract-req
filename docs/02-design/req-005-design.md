# REQ-005 설계 — 엑셀 다운로드

> 통합 설계 문서 참조: `req-all-design.md`, `req-all-data-design.md`

## 담당 범위

REQ-005-01 ~ REQ-005-03: 1단계(원본) / 2단계(원본+상세) 엑셀 다운로드

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/download?stage=1` | 1단계 엑셀 (원본만) |
| GET | `/api/v1/download?stage=2` | 2단계 엑셀 (원본 + 상세) |

응답: `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

## 엑셀 출력 스펙

### 1단계 엑셀 (원본 추출)
| 컬럼 | 내용 |
|------|------|
| A: 요구사항 ID | SFR-001, MHR-001 ... |
| B: 분류 | 기능 요구사항, 유지관리 인력 요구사항 ... |
| C: 명칭 | 지원포털 기능 개선 ... |
| D: 내용 | 세부내용 전문 |

### 2단계 엑셀 (원본 + 상세)
| 컬럼 | 내용 |
|------|------|
| A: 구분 | `원본` / `상세` |
| B: 요구사항 ID | SFR-001 / REQ-001-01 |
| C: 상위 ID | (원본은 공백, 상세는 SFR-001) |
| D: 분류 | 분류명 |
| E: 명칭 | 명칭 |
| F: 내용 | 내용 |

레이아웃: 원본 행(흰 배경) 다음에 해당 상세 행들(연한 파란 배경) 인터리빙

## 서비스 모듈

- `ExcelExportService.export(session_id, stage)` — openpyxl로 xlsx 생성
- 수정된 상세요구사항은 SessionStore에서 최신 값 사용

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-005-01 | `ExcelExportService.export(stage=1)` | 4컬럼 xlsx, 원본 행 수 일치 |
| UT-005-02 | `ExcelExportService.export(stage=2)` | 6컬럼 xlsx, 원본+상세 인터리빙 |
| UT-005-03 | `GET /api/v1/download` | Content-Type 헤더 xlsx 확인 |
| UT-005-04 | 수정 반영 | 채팅 수정 후 2단계 엑셀에 수정값 포함 |
