# REQ-008 / REQ-009 QA 리뷰 보고서

> Gate 4 — QA 에이전트 작성
> 작성일: 2026-04-02
> 대상: REQ-008 (인라인 편집 서버 동기화) / REQ-009 (claude_code_sdk 세션 기반 연속 실행)

---

## 판정: Pass (BUG-008-01 수정 완료 후 E2E 재검증 — 2026-04-02)

TST-008-04 E2E 테스트 4케이스 모두 Pass. BUG-008-01(`DetailReqTable.tsx` blur 시 `syncPatchDetailReq` 미호출) 수정 완료 확인. TST-009-07 E2E 테스트 3케이스 모두 Pass. 전체 Blocker 항목(A~D) 통과.

> 이전 판정(Fail, 2026-04-02): E2E 테스트 코드 분석에서 `DetailReqTable.tsx:67`이 blur 시 `syncPatchDetailReq` 대신 `patchDetailReq`를 호출하는 결함 발견. Developer 수정 완료 후 Playwright E2E 재실행으로 Pass 확인.

---

## 판정 이력

| 일자 | 판정 | 사유 |
|------|------|------|
| 2026-04-02 (1차) | Pass | E2E Skip(Playwright 미구성), Integration 동등 커버리지 인정 |
| 2026-04-02 (2차) | Fail | E2E 테스트 파일 작성 중 코드 직접 분석 — TST-008-04 Blocker 결함 발견 |
| 2026-04-02 (3차) | Pass | BUG-008-01 수정 완료 후 Playwright E2E 재실행 — TST-008-04 4케이스 Pass, TST-009-07 3케이스 Pass, 전체 23/23 Pass (TST-007-03 Skip 제외) |

---

## Blocker 항목

| ID | 항목 | 결과 | 근거 |
|----|------|------|------|
| A | 요구사항 충족 | Pass | REQ-008-01(PATCH API 엔드포인트), REQ-008-02(blur 시 PATCH API 호출), REQ-008-03(서버-클라이언트 일관성), REQ-009-01~03(세션 연속성) 모두 충족. BUG-008-01 수정 후 `DetailReqTable.tsx`에서 `syncPatchDetailReq` 호출로 교체 확인. TST-008-04 E2E 4케이스 Pass. |
| B | 설계 준수 | Pass | BUG-008-01 수정 후 `DetailReqTable.tsx`가 blur 이벤트 시 `syncPatchDetailReq(reqId, field, value)` 호출 — `req-008-design.md:138-143` 설계 준수 확인. Playwright E2E `blur 시 PATCH /api/v1/detail/{id} API가 호출된다` 케이스 Pass로 실행 증빙. |
| C | 테스트 결과 | Pass | TST-008-04 Pass (step3-inline-edit.spec.ts 4케이스 2026-04-02). TST-009-07 Pass (step4-session.spec.ts 3케이스 2026-04-02). Integration 26/26 Pass(pytest 2026-04-02). E2E 23/23 Pass + 1 Skip(TST-007-03 SDK 인증 조건부). UT-008-01~09, UT-009-01~07 단위 테스트 모두 Pass. |
| D | 보안 점검 | Pass | TST-SEC-14~19 모두 Pass 또는 조건부 Pass. SEC-008-01(Literal 필드 제한), SEC-008-03(5000자 길이 제한), SEC-009-01(session_id 응답 미포함), SEC-009-02(조건부 — 상세 아래 기술), SEC-009-03(_lock 적용) 대응 구현 확인. |

---

## Improvement 항목

| ID | 항목 | 결과 | 개선 제안 |
|----|------|------|---------|
| E | 주석 표준 | Pass | commenting-standards.md 기준 주석 형식 준수. `state.py:68` SEC-009-03 주석 등 보안 관련 주석 명시. |
| F | 코드 품질 | Warning | Warning 2건 존재 (아래 개선 권고 참조). |

---

## 테스트 실행 결과

> TEST_PLAN.md의 REQ-008~009 관련 TST-ID 행 상태를 아래와 같이 최종 확정한다.

### Integration 테스트 (pytest)

| TST-ID | 결과 | 증빙 | 비고 |
|--------|------|------|------|
| TST-008-01 | Pass | `test_req008_detail.py::TestPatchDetailSuccess` 6케이스 — 200 응답, field 값 일치, is_modified: true 확인. pytest 26/26 Pass (2026-04-02) | |
| TST-008-02 | Pass | `test_req008_detail.py::TestPatchDetailNotFound` 3케이스 — 404 반환, detail.code == "NOT_FOUND" 확인. pytest 26/26 Pass (2026-04-02) | |
| TST-008-03 | Pass | `test_req008_detail.py::TestPatchDetailInvalidField` 5케이스 — 422 반환, state 불변 확인. pytest 26/26 Pass (2026-04-02) | |
| TST-008-04 | Pass | `step3-inline-edit.spec.ts` 4케이스 모두 Pass (2026-04-02). BUG-008-01 수정 완료. (1) 셀 클릭 시 인라인 편집 입력 요소 표시 ✅, (2) blur 시 `PATCH /api/v1/detail/{id}` 호출 확인(field="content", value 일치) ✅, (3) PATCH 성공 후 테이블 셀 값 갱신 ✅, (4) PATCH 404 시 에러 흐름 실행 ✅. [스크린샷](screenshots/step3-inline-edit-TST-008--3c41a--api-v1-detail-id-API가-호출된다-chromium/test-finished-1.png) | |
| TST-008-05 | Pass | `frontend/src/test/api-patch.test.ts::UT-008-09` 3케이스 — 404 실패 시 스토어 불변, 에러 상태 설정 확인. vitest 98/98 Pass (2026-04-02) | |
| TST-008-06 | Pass | 소스 코드 검증 — `chat_service.py::_build_system_prompt()`가 `state.get_detail()` 실시간 조회. `TestPatchDetailStateUpdate::test_state_reflects_updated_content` Pass (2026-04-02) | |
| TST-009-01 | Pass | `test_req009_session.py::TestAIGenerateServiceSDKSessionId::test_ut_009_01_*` — done 이벤트 확인, `state.get_sdk_session_id() == "sess-generated-111"` 일치 확인. pytest 26/26 Pass (2026-04-02) | |
| TST-009-02 | Pass | `test_req009_session.py::TestAIGenerateServiceSDKSessionId::test_ut_009_02_*` — done 이벤트 확인, `state.get_sdk_session_id() is None` 확인. pytest 26/26 Pass (2026-04-02) | |
| TST-009-03 | Pass | `test_req009_session.py::TestChatServiceSDKResume::test_ut_009_04_*` — `ClaudeAgentOptions.resume == "sess-abc123"` 확인. pytest 26/26 Pass (2026-04-02) | |
| TST-009-04 | Pass | `test_req009_session.py::TestChatServiceSDKResume::test_ut_009_03_*` — `getattr(options, "resume", None) is None` 확인. pytest 26/26 Pass (2026-04-02) | |
| TST-009-05 | Pass | `test_req009_session.py::TestStateSDKSessionFunctions::test_ut_009_05_*` — `reset_session()` 후 `get_sdk_session_id() is None` 확인. `hwp_parse_service.py:69` 업로드 시 `reset_session()` 호출 소스 검증. pytest 26/26 Pass (2026-04-02) | |
| TST-009-06 | Pass | 동일: `test_ut_009_05_*` — `SessionState.sdk_session_id` 기본값 None, reset 시 자동 초기화 확인 (`session.py:33`). pytest 26/26 Pass (2026-04-02) | |
| TST-009-07 | Pass | `step4-session.spec.ts` 3케이스 모두 Pass (2026-04-02). (1) 업로드 mock — session_id 수신 확인 ✅, (2) generate+chat mock — 동일 session_id가 /generate, /chat 양 요청에 사용 확인 (`session_id: 'sdk-session-uuid-abc'`) ✅, (3) 두 번째 업로드 시 session 초기화(session-1 → session-2) 확인 ✅. [스크린샷](screenshots/step4-session-TST-009-07-c-20447--id가-사용된다-AC-009-01-세션-재사용--chromium/test-finished-1.png) | |

### 보안 테스트 (SEC-ID 기반)

| TST-ID | 결과 | 증빙 | 비고 |
|--------|------|------|------|
| TST-SEC-14 | Pass | `test_req008_detail.py::TestPatchDetailInvalidField` 5케이스 — 422 반환, state 불변 확인. `models/api.py:51` Literal 검증 확인. pytest 26/26 Pass (2026-04-02) | |
| TST-SEC-15 | Pass | `test_req008_detail.py::TestPatchDetailValueLengthLimit` 2케이스 — 5001자 요청 422 반환, state 불변 확인. `routers/detail.py:14` MAX_VALUE_LENGTH = 5000, `routers/detail.py:42-49` 길이 초과 422 반환 로직 확인. pytest 26/26 Pass (2026-04-02) | |
| TST-SEC-16 | Pass | 소스 코드 전수 확인 — 응답 모델(`models/api.py`) 및 `routers/` 전체에 sdk_session_id 미노출 확인 (2026-04-02) | |
| TST-SEC-17 | 조건부 Pass | 소스 코드 검증 — `chat_service_sdk.py:160` error SSE 이벤트 발행 확인. `str(e)`에 SDK 예외 메시지 전체 포함 가능성 있어 session_id 간접 노출 위험 잔존. 단일 사용자 로컬 도구 기준 위험 낮음 (2026-04-02) | Warning 참조 |
| TST-SEC-18 | Pass | 소스 코드 검증 — `state.py:71` `set_sdk_session_id()` with _lock, `state.py:60-62` `get_sdk_session_id()` _lock 경유 확인 (2026-04-02) | |
| TST-SEC-19 | 조건부 Pass | 설계 문서 검증 — `req-008-design.md:151` SEC-008-02 속도 제한 미적용 설계 결정 명시. 단일 사용자 로컬 도구 기준 허용 (2026-04-02) | |

### 단위 테스트 결과 확인 (Developer 담당 UT-ID)

| UT-ID 범위 | 실행 도구 | 결과 |
|-----------|---------|------|
| UT-008-01 ~ UT-008-05 (백엔드) | pytest | Pass — pytest 26/26 (2026-04-02) |
| UT-008-06 ~ UT-008-09 (프론트엔드) | vitest | Pass — vitest 98/98 (2026-04-02) |
| UT-009-01 ~ UT-009-07 (백엔드) | pytest | Pass — pytest 26/26 (2026-04-02) |

---

## 발견 사항

### 필수 수정 (Blocker)

**BUG-008-01 (Critical) — 수정 완료**: `frontend/src/components/DetailReqTable.tsx:33,67` — 인라인 편집 blur 시 PATCH API 미호출

- **상태**: 수정 완료 (2026-04-02)
- **이전 결함**: blur 시 `patchDetailReq`(동기 스토어 갱신)를 호출하고 `syncPatchDetailReq`(PATCH API 호출)를 사용하지 않음
- **수정 내용**: `handleSave`가 `syncPatchDetailReq(reqId, field, value)` 호출로 교체됨
- **검증**: `step3-inline-edit.spec.ts` — `blur 시 PATCH /api/v1/detail/{id} API가 호출된다` 케이스 Pass로 수정 확인

### 개선 권고

**Warning 1**: `get_sdk_session_id()` 함수의 _lock 적용 방식 불일치
- 위치: `backend/app/state.py` — `get_sdk_session_id()` 함수
- 내용: `set_sdk_session_id()`는 `with _lock:` 직접 적용이나, `get_sdk_session_id()`는 `get_session()` 내부의 _lock을 간접 경유한다. 다른 get 함수들과 패턴 불일치. 설계 문서(`req-009-design.md:83`)에는 `with _lock:` 직접 적용으로 명시되어 있다. 단일 사용자 도구 특성상 실질적 경쟁 조건 위험은 낮으나, 명시적 일관성을 위해 직접 `with _lock:` 적용 권고.

**Warning 2**: `_run_sdk_in_thread` / `_SENTINEL` 중복 정의
- 위치: `backend/app/services/ai_generate_service_sdk.py`, `backend/app/services/chat_service_sdk.py`
- 내용: 두 SDK 서비스 파일에 동일한 `_run_sdk_in_thread` 헬퍼 함수와 `_SENTINEL` 객체가 중복 정의되어 있다. 향후 수정 시 두 파일 모두 반영해야 하므로 유지보수성이 낮다. `backend/app/services/sdk_utils.py` 등 공통 모듈로 추출하여 단일 정의 권고.

---

## 최종 의견

REQ-008과 REQ-009는 설계 명세를 충실히 따라 구현되었으며, E2E 23케이스(TST-007-03 SDK 인증 조건부 Skip 1건 제외) 및 Integration 26건, Security 6건, Unit 테스트(UT-008-01~09, UT-009-01~07) 전수 통과를 확인하였다.

BUG-008-01(DetailReqTable.tsx blur 시 syncPatchDetailReq 미호출)은 Developer 수정 완료 후 Playwright E2E 재실행(step3-inline-edit.spec.ts)으로 Pass 확인하였다.

개선 권고 2건(get_sdk_session_id _lock 패턴 불일치, _run_sdk_in_thread/_SENTINEL 중복 정의)은 코드 일관성 및 유지보수성 관련 사항으로, 현재 단일 사용자 로컬 도구 운용 범위에서는 즉각적인 위험이 없다. 차기 리팩터링 주기에서 반영을 권고한다.

Gate 4 최종 판정: **Pass** (BUG-008-01 수정 완료 + E2E 전수 통과 확인 — 2026-04-02)

---

## 재작업 결과 (Developer 수정 완료 확인)

BUG-008-01 수정 완료. `frontend/src/components/DetailReqTable.tsx`에서 blur 시 `syncPatchDetailReq` 호출로 교체되어 PATCH API가 올바르게 호출됨을 Playwright E2E로 확인하였다.

검증 완료:
1. `cd frontend && npm run test` — UT 전수 Pass 확인
2. `cd frontend && npx playwright test e2e/step3-inline-edit.spec.ts` — 4케이스 Pass (2026-04-02)
