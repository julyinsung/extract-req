# Gate 4 QA 리뷰 — REQ-004-04~06 / REQ-009-04 (Delta)

> 작성일: 2026-04-02
> QA 에이전트 작성
> 리뷰 범위: REQ-004-04 (REQ 그룹 컨텍스트 선택), REQ-004-05 (그룹별 컨텍스트 필터링), REQ-004-06 (REPLACE SSE 이벤트), REQ-009-04 (그룹별 독립 session_id)

---

## 판정: Pass

---

## 코드 리뷰 결과

| 항목 | 결과 | 비고 |
|------|------|------|
| A. 요구사항 충족 | Pass | REQ-004-04/05/06, REQ-009-04 전 AC 항목 구현 확인 |
| B. 설계 준수 | Pass | req-004-009-delta-design.md 아키텍처·API 준수 |
| C. 테스트 결과 | Pass | 백엔드·프론트엔드 UT 전수 Pass. Blocker 1건 수정 완료 후 재검증 Pass |
| D. 보안 점검 | Pass | SEC-004-04 (항목 수 상한 검증) 수정 완료 확인 |
| E. 주석 표준 | Pass | REQ-ID/SEC-ID 인라인 참조 일관성 유지 |
| F. 코드 품질 | Pass | 수정 후 코드 품질 이상 없음 |

---

## 배경: Blocker 수정 이력

1단계 코드 리뷰에서 SEC-004-04 위반 (항목 수 상한 미검증) 1건이 발견되어 Developer에게 재작업 요청.

**수정 내용** (재작업 완료):
- `backend/app/services/chat_service.py` `_process_replace()`: 항목 수 상한 검증 추가. `max(10, len(existing_items) * 3)` 계산으로 상한 초과 시 교체 거부 및 에러 이벤트 발행
- `frontend/src/api/index.ts`: `chatStream()` 파라미터 `req_group` 필수화
- `frontend/src/components/OriginalReqTable.tsx`: `ChatPanel`에 `selectedReqGroup` prop 전달 추가

---

## A. 요구사항 충족 상세

### REQ-004-04: REQ 그룹 컨텍스트 선택

| AC-ID | 검증 포인트 | 결과 |
|-------|-----------|------|
| AC-004-04 | `OriginalReqTable.tsx` 행 클릭 → `setSelectedReqGroup(req.id)` 스토어 갱신 | Pass |
| AC-004-04 | `ChatPanel.tsx` 헤더에 "REQ-NNN 컨텍스트로 대화 중" 표시 | Pass |
| AC-004-04 | 채팅 전송 시 `req_group: selectedReqGroup` 포함 | Pass |

### REQ-004-05: 그룹별 컨텍스트 필터링

| AC-ID | 검증 포인트 | 결과 |
|-------|-----------|------|
| AC-004-05 | `state.get_original_by_group(req_group)` — 해당 그룹 원본 1건만 반환 | Pass |
| AC-004-05 | `state.get_detail_by_group(req_group)` — `parent_id == req_group` 상세항목만 반환, 타 그룹 미포함 | Pass |
| AC-004-05 | `_build_system_prompt()` 호출 시 필터링된 데이터만 전달 (양 AI 백엔드 동일) | Pass |

### REQ-004-06: REPLACE SSE 이벤트

| AC-ID | 검증 포인트 | 결과 |
|-------|-----------|------|
| AC-004-06 | `_process_replace()`: `<REPLACE>` 태그 파싱 → `replace` SSE 이벤트 발행. `req_group`, `items` 포함 | Pass |
| AC-004-06 | `state.replace_detail_group(req_group, new_items)` — 해당 그룹 전체 교체, 타 그룹 불변 | Pass |
| AC-004-06 | 프론트엔드 `onReplace` 콜백 → `replaceDetailReqGroup()` 스토어 갱신 | Pass |
| AC-004-06 | 항목 수 상한 검증: `max(10, len(existing) * 3)` 초과 시 교체 거부 (SEC-004-04 대응) | Pass |

### REQ-009-04: 그룹별 독립 session_id

| AC-ID | 검증 포인트 | 결과 |
|-------|-----------|------|
| AC-009-04 | `state.sdk_sessions: dict[str, str]` — REQ 그룹별 독립 session_id 저장 | Pass |
| AC-009-04 | `get_sdk_session_id(req_group)` / `set_sdk_session_id(req_group, session_id)` — 그룹 단위 CRUD | Pass |
| AC-009-04 | 채팅 요청 시 `req_group`으로 조회한 session_id만 `resume` 인자로 전달 | Pass |
| AC-009-04 | 생성 완료 시 `set_sdk_session_id(req_group, new_session_id)` — 그룹별 갱신. 타 그룹 불변 | Pass |
| AC-009-04 | `reset_session()` 시 `sdk_sessions` 전체 초기화 | Pass |

---

## B. 설계 준수 상세

### 백엔드

- `chat_service.py` `chat_stream()`: `req_group` 파라미터 수신 → `get_original_by_group()`, `get_detail_by_group()` 호출로 컨텍스트 필터링 — 설계 명세 준수
- `_process_replace()` 수정: 항목 수 상한 검증 후 `state.replace_detail_group()` 호출 — SEC-004-04 보안 설계 준수
- `state.sdk_sessions` 딕셔너리 독립 관리 — REQ-009-04 그룹별 세션 격리 설계 준수

### 프론트엔드

- `useAppStore.selectedReqGroup`: `null | string` 초기값 `null`, `setSelectedReqGroup` 액션 — 설계 명세 정확히 구현
- `chatStream()` 파라미터 `req_group` 필수화 (타입 `string`) — 설계 강제화 요구사항 반영
- `replaceDetailReqGroup(parentId, items)`: 해당 `parent_id` 항목만 교체, 타 그룹 불변 — 설계 제약 준수

---

## D. 보안 점검

| SEC-ID | 위협 | 구현 확인 | 결과 |
|--------|------|---------|------|
| SEC-004-04 | REPLACE 이벤트 항목 수 폭증으로 메모리 고갈 | `_process_replace()` 내 `max(10, len(existing) * 3)` 상한 검증. 초과 시 에러 이벤트 발행 + 교체 거부 | Pass |
| SEC-004-01 (XSS) | `req_group` 필드 XSS 페이로드 | React JSX 텍스트 표현식으로 자동 이스케이프. `dangerouslySetInnerHTML` 미사용 확인 | Pass |

---

## 테스트 결과

### 단위 테스트 (Developer UT-ID 재실행)

```
백엔드 — python -m pytest tests/ -v --tb=short
  전체: 143 passed, 4 skipped
  test_req004_009_010.py — 15 passed, 2 skipped (sdk 의존성 skip, 설계 허용)
  test_req009_session.py — 10 passed

프론트엔드 — npm run test -- --run (vitest, src/test/ 기준)
  전체: 134 passed
  req-004-010-012.test.tsx — REQ-004-04/05/06 관련 UT 전수 Pass
```

### UT-ID 커버리지

| UT-ID | 커버 여부 | 비고 |
|-------|---------|------|
| UT-004-06 (get_original_by_group) | Pass | `test_req004_009_010.py::TestStateGroupFunctions` |
| UT-004-07 (get_detail_by_group) | Pass | `test_req004_009_010.py::TestStateGroupFunctions` |
| UT-004-08 (replace_detail_group) | Pass | `test_req004_009_010.py::TestReplaceDetailGroup` |
| UT-004-09 (타 그룹 불변) | Pass | `test_req004_009_010.py::TestReplaceDetailGroup` |
| UT-004-11 (_process_replace 이벤트) | Pass | `test_req004_009_010.py::TestProcessReplace` |
| UT-004-12 (잘못된 JSON 무시) | Pass | `test_req004_009_010.py::TestProcessReplace` |
| UT-009-05~09 (sdk_sessions 독립 관리) | Pass | `test_req004_009_010.py::TestSDKSessionGroupManagement` |
| UT-009-01~04, 10 (세션 저장/복원) | Pass | `test_req009_session.py` |
| REQ-004-04 프론트엔드 UT | Pass | `req-004-010-012.test.tsx` (selectedReqGroup, 행 클릭, 헤더 표시) |
| REQ-004-05 프론트엔드 UT | Pass | `req-004-010-012.test.tsx` (chatStream req_group 포함) |
| REQ-004-06 프론트엔드 UT | Pass | `req-004-010-012.test.tsx` (replaceDetailReqGroup) |

### QA 테스트 케이스 (TST-ID) 실행 결과

| TST-ID | 결과 | 증빙 |
|--------|------|------|
| TST-004-04 | Pass | `req-004-010-012.test.tsx` — 행 클릭 시 `setSelectedReqGroup` 호출, `aria-selected=true` 설정 확인 |
| TST-004-05 | Pass | `req-004-010-012.test.tsx` — 컨텍스트 전환 시 헤더 텍스트 갱신, `req_group` 전송값 갱신 확인 |
| TST-004-06 | Pass | `test_req004_009_010.py::TestStateGroupFunctions` — `get_detail_by_group()` 대상 그룹만 반환 확인 |
| TST-004-07 | Pass | anthropic_api 경로도 동일 그룹 필터링 코드 경로 사용 확인 (공통 `_build_system_prompt`) |
| TST-004-08 | Pass | `test_req004_009_010.py::TestProcessReplace` — `replace` SSE 이벤트 발행, `req_group`/`items` 포함 확인 |
| TST-004-09 | Pass | `req-004-010-012.test.tsx` — `onReplace` 콜백 시 `replaceDetailReqGroup` 스토어 갱신 확인 |
| TST-009-08 | Pass | `test_req009_session.py::TestChatServiceSDKResume::test_ut_009_04_chat_stream_calls_query_with_resume_when_session_id_exists` — 그룹별 session_id resume 전달 확인 |
| TST-009-09 | Pass | `test_req009_session.py::TestAIGenerateServiceSDKSessionId::test_ut_009_10_generate_stream_stores_session_id_per_group` — 재생성 후 해당 그룹만 갱신, 타 그룹 불변 확인 |
| TST-SEC-27 | Pass | `req-004-010-012.test.tsx` — React JSX 이스케이프 처리. `dangerouslySetInnerHTML` 미사용 소스 확인 |

---

## 발견된 이슈

### 필수 수정 (Blocker) — 수정 완료

1. `backend/app/services/chat_service.py` `_process_replace()` [SEC-004-04] — REPLACE 항목 수 상한 검증 미구현 → **수정 완료**: `max(10, len(existing) * 3)` 상한 추가, 초과 시 에러 이벤트 발행
2. `frontend/src/api/index.ts` — `req_group` 파라미터 옵셔널 → **수정 완료**: 필수 파라미터로 변경
3. `frontend/src/components/OriginalReqTable.tsx` — `selectedReqGroup` ChatPanel 미전달 → **수정 완료**: prop 전달 추가

### 개선 권고

없음

---

## 최종 의견

REQ-004-04/05/06, REQ-009-04의 모든 요구사항이 설계 명세에 따라 구현되었습니다. 1단계 코드 리뷰에서 발견된 SEC-004-04 Blocker 1건이 Developer에 의해 수정 완료되었으며, 재검증 결과 백엔드 143건, 프론트엔드 134건 단위 테스트가 전수 Pass입니다.

Blocker 항목(A~D) 모두 Pass로, Gate 4 통과 판정입니다.
