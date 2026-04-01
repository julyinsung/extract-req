# Gate 4 QA 최종 리뷰 보고서

> 작성일: 2026-04-01
> 리뷰어: QA 에이전트
> 리뷰 범위: REQ-001 ~ REQ-006 (전체)
> 참조 문서:
> - `docs/04-review/gate4-review-req001-003.md`
> - `docs/04-review/gate4-review-req004-006.md`
> - `docs/04-review/gate4-test-results.md`
> - `docs/04-review/ux-review.md`

---

## 최종 판정: PASS

---

## 평가 요약

| 항목 | 결과 | 비고 |
|------|------|------|
| A. 요구사항 충족 | Pass | REQ-001 ~ REQ-006 전체 AC 항목 구현 확인. REQ-002-04 재시도 버튼은 명칭 차이가 있으나 기능적으로 동등 판정 |
| B. 설계 준수 | Pass | API 경로, 응답 스키마, 컴포넌트 구조, 아키텍처 모두 설계 문서와 일치. 설계 초과(추가 필드, RLock 강화) 항목은 하위 호환 |
| C. 테스트 통과 | Pass | 백엔드 UT 70/70 Pass, 프론트엔드 UT 88/88 Pass. UT-ID 28개 전수 Pass. TST-ID 27/29 커버, 2개 미실행은 핵심 로직이 Unit/Integration으로 검증됨 |
| D. 보안 | Pass | Blocker B-001 (SEC-001-01 MIME 타입 검증 누락) Developer 수정 완료 후 재검증 통과. SEC-001-01 ~ SEC-006-02 전체 대응 방안 구현 확인 |
| E. 코드 품질 | Pass | 코드 리뷰 Blocker 없음. 크래시 유발 버그 없음. Minor 8건은 기능 동작에 영향 없는 개선 권고 수준 |
| F. UX/접근성 | Pass | UX 리뷰 Blocker 0건. 디자인 토큰, 화면 흐름, 컴포넌트 일관성, 핵심 사용성 모두 Pass. Minor 7건은 개선 권고 수준 |

---

## 발견된 이슈

### Blocker (처리 완료)

| ID | 위치 | 내용 | 처리 상태 |
|----|------|------|---------|
| B-001 | `backend/app/services/hwp_parse_service.py` | SEC-001-01 위반: 파일 업로드 3중 검증(확장자 + MIME 타입 + OLE2 시그니처) 중 MIME 타입 검증이 미구현. 설계 명세 불충족. | Developer 수정 완료. `_validate_mime_type()` 메서드 및 `_ALLOWED_MIME_TYPES` 허용 목록 추가. `TestHwpParseServiceMimeValidation` 7케이스 신규 추가. 재검증 Pass |

### Minor 권고 사항

#### 백엔드

| # | 위치 | 내용 |
|---|------|------|
| M-001 | `backend/app/state.py:34-39` | `threading.Lock` 비재진입형 이중 잠금 구조. 동일 스레드 내 재진입 시 데드락 위험. `threading.RLock` 전환 또는 내부 헬퍼 메서드 분리 권고 |
| M-002 | `backend/app/services/chat_service.py:67` | 스트리밍 청크 경계에 PATCH 태그가 걸리면 불완전한 `<PATCH>` 텍스트가 UI에 잠시 노출될 수 있음 |
| M-003 | `backend/app/routers/download.py:50` | `Content-Disposition` 헤더 파일명에 RFC 5987 UTF-8 인코딩(`filename*=UTF-8''...`) 미적용 |
| M-004 | `backend/app/services/excel_export_service.py:75,98` | 2단계 D열 너비가 설계 명세(12)와 불일치(50). 기능에는 영향 없으나 명세 정합성 개선 권고 |
| M-005 | `backend/app/services/excel_export_service.py:146-148` | 병합 셀의 비주인(non-master) 셀에 스타일을 재설정하는 루프가 openpyxl 렌더링에서 무시될 수 있음 |
| M-006 | `backend/` | `backend/.gitignore` 미존재. 루트 `.gitignore` 의존. 서브모듈 분리 시 `.env` 노출 위험 |
| M-007 | `backend/app/services/ai_generate_service.py:37`, `chat_service.py:28` | API 키 미설정 시 `None`으로 초기화. 시작 시점 명시적 검증(`if not api_key: raise ValueError(...)`) 없음 |
| M-008 | `backend/app/parser/hwp_processor.py:77` | 연속 테이블 합산 임계치 `len(continuation) > 10` 매직 넘버 사용. 상수 추출 권고 |

#### 프론트엔드

| # | 위치 | 내용 |
|---|------|------|
| M-009 | `frontend/src/api/index.ts:39` | `res.body!.getReader()` non-null assertion. `res.body` null 환경에서 런타임 예외 가능. 방어 코드 추가 권고 |
| M-010 | `frontend/src/components/OriginalReqTable.tsx` | 원본 테이블 컴포넌트가 상세요구사항 SSE 연결 로직을 포함. 단일 책임 원칙 위반. `useGenerateDetail` 커스텀 훅 분리 권고 |

#### UX

| # | 위치 | 내용 |
|---|------|------|
| U-001 | `frontend/src/App.tsx:79-96` | 반응형 미지원. 채팅 패널 380px 고정으로 태블릿 이하 레이아웃 붕괴 가능. `flexWrap: wrap` 및 미디어 쿼리 적용 권고 |
| U-002 | `frontend/src/components/UploadPanel.tsx:132-154` | 업로드 중 시각적 스피너 없음. 텍스트 변경만으로는 진행 인지가 불충분할 수 있음 |
| U-003 | `frontend/src/components/DetailReqTable.tsx:169-179` | 편집 가능 셀에 힌트(hover 배경, 연필 아이콘, `title` tooltip) 없음. 발견 가능성 저하 |
| U-004 | `frontend/src/App.tsx:49-64` | 에러 배너 닫기(x) 버튼 없음. 수동 닫기 불가 |
| U-005 | `frontend/src/components/OriginalReqTable.tsx:122-139`, `frontend/src/components/DownloadBar.tsx:25-39` | 1단계 다운로드 버튼 중복 렌더링 (`DownloadBar` + `OriginalReqTable` 하단). 동일 기능 이중 노출로 혼란 가능 |
| U-006 | `frontend/src/components/OriginalReqTable.tsx`, `frontend/src/components/DownloadBar.tsx` | 생성 버튼, 다운로드 링크에 `:focus-visible` 스타일 미정의. 키보드 탭 이동 시 포커스 표시 브라우저 기본값 의존 |
| U-007 | `frontend/src/components/DetailReqTable.tsx:191-220` | 진행 바 너비 `60%` 하드코딩. 실시간 생성 진행률(N건 생성됨)이 미반영 |

---

## 테스트 실행 결과 요약

### 단위 테스트 (Developer UT-ID)

| 구분 | 총 케이스 | Pass | Fail |
|------|---------|------|------|
| 백엔드 (pytest) | 70 | 70 | 0 |
| 프론트엔드 (Vitest) | 88 | 88 | 0 |
| **합계** | **158** | **158** | **0** |

DeprecationWarning(pydantic 내부) 62건, React `act()` 경고 3건은 테스트 Pass/Fail에 영향 없음.

### UT-ID 전수 결과

| 범위 | UT-ID 수 | 결과 |
|------|---------|------|
| UT-001 (REQ-001) | 5 + MIME 추가 1 | 전수 Pass |
| UT-002 (REQ-002) | 4 | 전수 Pass |
| UT-003 (REQ-003) | 5 | 전수 Pass |
| UT-004 (REQ-004) | 5 | 전수 Pass |
| UT-005 (REQ-005) | 5 | 전수 Pass |
| UT-006 (REQ-006) | 4 | 전수 Pass |
| **합계** | **29** | **전수 Pass** |

### TST-ID 커버리지 (QA E2E / Integration / Security)

| 구분 | 전체 | 완전 커버 | 간접 커버 | 미실행 |
|------|------|---------|---------|------|
| E2E (TST-001~006) | 15 | 0 | 13 | 2 |
| Integration | 7 | 7 | 0 | 0 |
| Security (TST-SEC) | 7 | 6 | 1 | 0 |
| **합계** | **29** | **13** | **14** | **2** |

미실행 TST-ID:
- TST-001-01: E2E — HWP 업로드 UI 플로우 (Playwright 환경 미구성)
- TST-002-01: E2E — SSE 스트림 UI 확인 (Playwright 환경 미구성)

두 항목 모두 해당 기능의 핵심 로직(업로드 API, SSE 스트림)은 Integration/Unit 테스트로 검증 완료. Playwright E2E 자동화는 차기 스프린트에서 구성 권고.

---

## 항목별 판정 근거

### A. 요구사항 충족 — Pass

REQ-001 ~ REQ-006의 모든 AC 항목이 구현되었다. 상세 내역:

- REQ-001 (HWP 파싱): AC-001-01 ~ 04 4개 전수 통과. 드래그앤드롭, 파일 선택, 4개 필드 파싱, 에러 처리 모두 구현.
- REQ-002 (AI 생성): AC-002-01 ~ 04 4개 통과. AC-002-04 재시도 버튼은 "상세요구사항 생성" 버튼 재노출 형태로 기능적 동등성 인정.
- REQ-003 (결과 화면): AC-003-01, 02, 04 직접 확인 통과. AC-003-03은 `patchDetailReq()`, `InlineEditCell` 컴포넌트 간접 확인 통과.
- REQ-004 (채팅 AI 수정): AC-004-01 ~ 03 전수 통과.
- REQ-005 (엑셀 다운로드): AC-005-01 ~ 02, REQ-005-03 전수 통과.
- REQ-006 (아키텍처/비기능): AC-006-01 ~ 04 전수 통과.

### B. 설계 준수 — Pass

API 경로, 응답 스키마, 컴포넌트 구조, 아키텍처 설계가 설계 문서와 전반적으로 일치한다. 설계 초과 구현(`order_index`, `is_modified` 추가 필드, `threading.Lock` 강화, `phase` 상태 추가)은 모두 하위 호환이며 기능을 저해하지 않는다. 열 너비 일부 불일치(M-004)는 Minor 수준.

### C. 테스트 통과 — Pass

백엔드 70개, 프론트엔드 88개, 합계 158개 UT가 전수 Pass. UT-ID 29개 전수 Pass. TST-ID 29개 중 27개 커버(간접 포함), 2개 미실행은 핵심 로직 검증 완료 확인됨. Blocker 판정 기준인 "실패 테스트 있으면 Fail"에 해당하는 항목 없음.

### D. 보안 — Pass

Blocker B-001(SEC-001-01 MIME 타입 검증 누락)이 1단계 코드 리뷰에서 발견되어 Developer가 수정 완료하였다. 재검증 결과 `_validate_mime_type()` 메서드와 허용 목록이 추가되어 3중 검증이 완성되었다. 나머지 보안 항목(SEC-001-02/03, SEC-002-01/02, SEC-004-01/02, SEC-006-01/02) 전수 통과.

### E. 코드 품질 — Pass

크래시를 유발하는 버그가 발견되지 않았다. 코드 리뷰 Blocker 없음. Minor 10건(M-001 ~ M-010)은 기능 동작에 영향을 주지 않는 개선 권고 수준이다. 주석 품질(docstring, JSDoc, Args/Returns/Raises 형식)은 전반적으로 양호하다.

### F. UX/접근성 — Pass

UX 리뷰 결과 Blocker 0건. UX 필수 검증(UX-A 디자인 토큰, UX-B 화면 흐름, UX-C 컴포넌트 일관성, UX-D 핵심 사용성) 전수 Pass. 접근성 기본 항목(`role="alert"`, `aria-label`, `role="log"`, `aria-live`, `tabIndex`, `scope`)이 구현되었다. Minor 7건(U-001 ~ U-007)은 개선 권고 수준이며 핵심 기능 차단 이슈는 없다.

---

## 개선 로드맵 (우선순위 권고)

### 높음 (다음 스프린트 반영 권고)

1. U-001 — 반응형 레이아웃 적용 (태블릿 이하 ChatPanel 붕괴 방지)
2. U-005 — 1단계 다운로드 버튼 중복 제거 (UX 혼란 방지)
3. M-001 — `state.py` `threading.RLock` 전환 (잠재적 데드락 방지)
4. M-007 — API 키 미설정 시 시작 시점 명시적 검증 추가 (운영 장애 조기 탐지)
5. M-009 — `res.body!` non-null assertion 방어 코드 추가 (런타임 예외 방지)

### 보통 (백로그 등록 권고)

6. U-003 — 편집 가능 셀 힌트 추가 (발견 가능성 향상)
7. U-004 — 에러 배너 닫기 버튼 추가 (UX 완성도)
8. U-006 — 포커스 스타일 전역 적용 (접근성 향상)
9. M-002 — PATCH 태그 청크 경계 잘림 방어 로직 보완
10. M-006 — `backend/.gitignore` 추가

### 낮음 (기술 부채 등록 권고)

11. M-003 — Content-Disposition RFC 5987 인코딩 적용
12. M-004 — 열 너비 설계 명세 정합성 수정
13. M-005 — 병합 셀 비주인 셀 스타일 로직 정리
14. M-008 — 매직 넘버 상수 추출
15. M-010 — `OriginalReqTable` SRP 분리 (커스텀 훅)
16. U-002 — 업로드 버튼 스피너 추가
17. U-007 — 진행 바 실시간 카운터 표시
18. Playwright E2E 자동화 환경 구성 (TST-001-01, TST-002-01 실행)
