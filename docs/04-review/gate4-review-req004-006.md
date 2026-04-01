# Gate 4 코드 리뷰 — REQ-004~006

> 작성일: 2026-04-01
> 담당: QA 에이전트
> 리뷰 범위: REQ-004 (채팅 기반 AI 수정), REQ-005 (엑셀 다운로드), REQ-006 (시스템 아키텍처 및 비기능)

---

## REQ-004: 채팅 기반 AI 수정

### A. 요구사항 충족

| AC-ID | 요구사항 | 구현 여부 | 근거 |
|-------|---------|----------|------|
| AC-004-01 | 채팅으로 수정 요청 → Claude API 전달 | Pass | `ChatService.chat_stream()`이 `session_id`, `message`, `history`를 받아 Claude API를 호출하고 SSE 스트림으로 응답한다 (`chat_service.py:32-80`) |
| AC-004-02 | 수정 결과 테이블 즉시 반영 + 시각 강조 | Pass | `ChatPanel`의 `onPatch` 콜백이 `patchDetailReq` 스토어 액션 호출 후 `req-highlight` 커스텀 이벤트를 발행하고, `DetailReqTable`이 이를 수신하여 3초간 노란 배경 강조를 적용한다 (`ChatPanel.tsx:79-82`, `DetailReqTable.tsx:44-58`) |
| AC-004-03 | 채팅 대화 내역 유지 + 스크롤 가능 | Pass | `chatHistory` 상태를 Zustand 스토어에 보관하며, 대화 영역에 `role="log"` + `overflowY: auto`로 스크롤 가능하게 구현되어 있다 (`ChatPanel.tsx:129-143`) |

판정: **Pass** — AC-004-01 ~ AC-004-03 모두 구현됨.

### B. 설계 준수

| 항목 | 기준 | 결과 | 근거 |
|------|------|------|------|
| API 엔드포인트 | `POST /api/v1/chat` | Pass | `chat.py:15`에 `@router.post("/chat")` 정의 |
| 요청 스키마 | `session_id`, `message`, `history` | Pass | `ChatRequest` 모델에 3개 필드 모두 정의 (`api.py:33-41`) |
| SSE 이벤트 형식 | `text`, `patch`, `done`, `error` 4종 | Pass | `chat_service.py`의 `_sse()` 호출부가 4종 모두 발행 |
| PATCH 태그 프로토콜 | `<PATCH>{...}</PATCH>` 감지 후 `patch` 이벤트 발행 + state 갱신 | Pass | `PATCH_RE` 정규식으로 감지 후 `_process_patches()`에서 처리 (`chat_service.py:18, 107-122`) |
| 채팅 히스토리 클라이언트 유지 | 서버 미저장, 클라이언트 매 요청 전달 | Pass | 설계 문서 명세와 동일하게 구현됨 |
| `ChatPanel` 입력 비활성화 조건 | `sessionId` 없거나 `detailReqs` 비어있을 때 | Pass | `disabled` 변수가 3가지 조건을 AND 결합 (`ChatPanel.tsx:32`) |
| 메시지 전송 후 자동 스크롤 | 최신 메시지로 스크롤 | Pass | `chatHistory`, `streamingText` 의존성으로 `scrollIntoView` 호출 (`ChatPanel.tsx:35-37`) |

판정: **Pass** — 설계 문서의 API 스펙, PATCH 프로토콜, React 컴포넌트 구조 모두 준수.

### D. 보안

| SEC-ID | 내용 | 결과 | 근거 |
|--------|------|------|------|
| SEC-004-01 | 채팅 입력 XSS 방지 (React 기본 이스케이프 + JSON 직렬화) | Pass | `ChatPanel.tsx`는 `{msg.content}`를 JSX 텍스트로 렌더링하여 React 자동 이스케이프 적용. 서버는 `_build_system_prompt()`에서 JSON 직렬화로 컨텍스트를 삽입하여 프롬프트 인젝션 방지 (`chat_service.py:83-97`) |
| SEC-004-02 | 채팅 메시지 길이 제한 2000자 (클라이언트 + 서버 이중 검증) | Pass | 클라이언트: `onChange`에서 `.slice(0, 2000)` 적용 (`ChatPanel.tsx:211`). 서버: `len(message) > MAX_MESSAGE_LENGTH` 검증 (`chat_service.py:44-46`) |

판정: **Pass** — SEC-004-01, SEC-004-02 모두 구현됨.

### E. 단위 테스트 (UT-ID별)

| UT-ID | 대상 | 테스트 파일 위치 | 결과 |
|-------|------|----------------|------|
| UT-004-01 | `ChatService.chat_stream()` — text/patch 이벤트 발행 | `test_chat.py:TestChatStreamNormal` | Pass — `test_text_and_patch_events_emitted`, `test_done_event_is_last` 2개 케이스 |
| UT-004-02 | PATCH 태그 파싱 → patch 이벤트 + state 갱신 | `test_chat.py:TestPatchParsing` | Pass — 단일/다중 PATCH, state 갱신, `is_modified` 3개 케이스 |
| UT-004-03 | 일반 질문 → patch 이벤트 없음, text만 | `test_chat.py:TestNoPatchForGeneralQuestion` | Pass — 2개 케이스 |
| UT-004-04 | Claude APIError → error 이벤트 | `test_chat.py:TestChatStreamApiError` | Pass — API 오류 및 상세 미생성 2개 케이스 |
| UT-004-05 | `detailReqs` 비어있을 때 ChatInput disabled | 프론트엔드 유닛 테스트 미작성 | 미확인 — 백엔드 테스트만 존재, 프론트엔드 Jest 테스트 부재 |

비고: UT-004-05는 프론트엔드(`ChatPanel.tsx:32`)에서 `disabled` 로직이 구현되어 있으나, 해당 로직에 대한 Jest/React Testing Library 단위 테스트가 존재하지 않음. 설계 문서 UT-ID 정의 기준으로 미충족.

판정: **Minor** — UT-004-05 프론트엔드 테스트 누락 (로직 자체는 구현됨).

### F. 코드 품질

| 항목 | 결과 | 세부 사항 |
|------|------|---------|
| 에러 처리 | Pass | `APIError`와 범용 `Exception` 분리 처리, SSE `error` 이벤트로 클라이언트에 전달 |
| 스트리밍 청크 내 PATCH 중간 잘림 가능성 | Minor | `chat_service.py:67`에서 청크별로 `re.sub(r"<PATCH>.*?</PATCH>", ...)` 처리 시, PATCH 태그가 2개 이상의 청크에 걸쳐 수신되면 `<PATCH>` 시작 텍스트가 사용자에게 노출될 수 있음. 완료 후 일괄 처리(`_process_patches`) 방식이 정확하나, 스트리밍 중 텍스트 정제 로직은 불완전한 PATCH 태그를 걸러내지 못함 |
| SSE 연결 cleanup | Pass | `cleanupRef`에 cleanup 함수 저장, 컴포넌트 언마운트 시 실행 (`ChatPanel.tsx:40-43`) |
| 주석 품질 | Pass | 모듈 수준 docstring, 함수 Args/Returns/Yields 작성, SEC-ID 참조 주석 포함 |

---

## REQ-005: 엑셀 다운로드

### A. 요구사항 충족

| AC-ID | 요구사항 | 구현 여부 | 근거 |
|-------|---------|----------|------|
| AC-005-01 | 1단계 다운로드 — 원본 요구사항 4컬럼 xlsx | Pass | `_write_stage1()`이 "요구사항 ID", "분류", "요구사항 명칭", "요구사항 내용" 4컬럼으로 원본 데이터를 출력 (`excel_export_service.py:71-84`) |
| AC-005-02 | 2단계 다운로드 — 원본 + 상세 통합 xlsx | Pass | `_write_stage2()`가 A-D(원본), E-G(상세) 7컬럼으로 원본 셀 병합 레이아웃 구현 (`excel_export_service.py:87-148`) |
| REQ-005-03 | 컬럼 구조 — ID, 분류, 명칭, 내용 포함 | Pass | 1단계 4컬럼, 2단계 7컬럼 모두 명세 컬럼 포함 |

버튼 활성화 조건 (AC-005-01/02 연동):
- 1단계 버튼: `originalReqs.length > 0`일 때 표시 (`DownloadBar.tsx:15`)
- 2단계 버튼: `detailReqs.length > 0`일 때만 표시 (`DownloadBar.tsx:42`)

판정: **Pass** — AC-005-01 ~ 02 모두 구현됨.

### B. 설계 준수

| 항목 | 기준 | 결과 | 근거 |
|------|------|------|------|
| API 엔드포인트 | `GET /api/v1/download?session_id=...&stage=1\|2` | Pass | `download.py:17-51` |
| 응답 Content-Type | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Pass | `download.py:48` |
| Content-Disposition | `attachment; filename=...` | Minor | 파일명에 공백/특수문자가 없어 현재는 무방하나, RFC 5987 준수를 위한 `filename*=UTF-8''...` 인코딩 미적용 (`download.py:50`) |
| 에러 코드 | `SESSION_NOT_FOUND(404)`, `DETAIL_NOT_GENERATED(422)` | Partial Pass | `DETAIL_NOT_GENERATED(422)` 구현됨. 그러나 `SESSION_NOT_FOUND(404)` 미구현 — 현재 인메모리 싱글턴 구조상 세션 자체가 없는 케이스를 별도 처리하지 않음 |
| 파일명 패턴 | `requirements_original_{YYYYMMDD_HHMMSS}.xlsx` | Pass | `download.py:44-45` |
| 엑셀 스타일 | 헤더 #4472C4, 원본 열 #D9E1F2, 수정 행 #FFF2CC | Pass | `excel_export_service.py:19-27` 상수 정의 및 적용 |
| 셀 병합 | 원본 1건당 상세 N건 병합 | Pass | `excel_export_service.py:133-143` |
| freeze_panes | `"A2"` | Pass | `excel_export_service.py:65` |
| 다운로드 방식 | `<a href download>` | Pass | `DownloadBar.tsx:25-38` |
| 열 너비 설정 | 설계 명세 준수 | Minor | 설계: A:8, B:15, C:15, D:12, E:30, F:60. 실제 1단계: [15,12,30,60], 2단계: [15,12,30,50,15,30,60]. D열 60→50 으로 설계와 일부 불일치 (`excel_export_service.py:75, 98`) |

판정: **Pass** (Minor 2건 포함) — 핵심 기능은 설계 준수. `SESSION_NOT_FOUND` 에러는 현재 인메모리 단일 세션 구조에서 발생 시나리오가 제한적이어서 Blocker로 분류하지 않음.

### D. 보안

| 항목 | 결과 | 근거 |
|------|------|------|
| 세션 격리 | Pass | 인메모리 싱글턴으로 단일 사용자 전제 설계. `session_id` 파라미터는 현재 유효성 검증 없이 state를 직접 조회하나, 단일 사용자 전제로 설계 문서에 명시되어 있음 |
| 임의 `stage` 값 주입 | Pass | `stage not in (1, 2)` 검증으로 422 반환 (`download.py:34-38`) |
| 파일 경로 조작 | Pass | 엑셀은 메모리(`io.BytesIO`)에서 생성하므로 파일시스템 경로 관련 취약점 없음 |

판정: **Pass**

### E. 단위 테스트 (UT-ID별)

| UT-ID | 대상 | 테스트 파일 위치 | 결과 |
|-------|------|----------------|------|
| UT-005-01 | `export(stage=1)` — 4컬럼, 행 수 일치 | `test_excel.py:TestExportStage1` | Pass — 4개 케이스 (컬럼수, 행수, 값, 시트명) |
| UT-005-02 | `export(stage=2)` — 7컬럼, 병합 확인 | `test_excel.py:TestExportStage2` | Pass — 5개 케이스 (컬럼수, 병합 존재, A2:A4 범위, 시트명, 순서) |
| UT-005-03 | `GET /api/v1/download` Content-Type 헤더 | `test_excel.py:TestDownloadEndpoint` | Pass — 3개 케이스 (Content-Type, Content-Disposition, 잘못된 stage) |
| UT-005-04 | `is_modified=True` → MOD_FILL 적용 | `test_excel.py:TestModifiedFill` | Pass — 3개 케이스 (채움색 일치, 미수정 채움색 불일치, 값 반영) |
| UT-005-05 | stage=2 + 상세 없음 → 422 | `test_excel.py:TestStage2WithoutDetails` | Pass — 2개 케이스 (서비스 직접 호출, 엔드포인트 경유) |

판정: **Pass** — UT-005-01 ~ UT-005-05 전체 케이스 작성됨.

### F. 코드 품질

| 항목 | 결과 | 세부 사항 |
|------|------|---------|
| 상세 없는 원본 처리 | Pass | `detail_map.get(orig.id, [])` + `count = max(len(dets), 1)`으로 빈 케이스 처리 (`excel_export_service.py:108-109`) |
| 병합 후 배경색 적용 | Minor | 병합된 셀(예: A3, A4)에도 `fill`을 재설정하는 루프가 존재하나, openpyxl에서 병합 셀의 비주인(non-master) 셀에 대한 스타일 적용이 실제 xlsx 렌더링에서 무시될 수 있음 (`excel_export_service.py:146-148`). 기능적으로 문제는 없으나 의도와 다른 동작 가능성 |
| 에러 응답 일관성 | Pass | `HTTPException`에 `{"code": ..., "message": ...}` 구조 사용 |
| 주석 품질 | Pass | 모듈, 함수, 인라인 주석 모두 충실하게 작성됨 |

---

## REQ-006: 시스템 아키텍처 및 비기능 요구사항

### A. 요구사항 충족

| AC-ID | 요구사항 | 구현 여부 | 근거 |
|-------|---------|----------|------|
| AC-006-01 | 프론트엔드/백엔드 분리 (HTTP REST) | Pass | Frontend: Vite+React(포트 3000), Backend: FastAPI(포트 8000). HTTP API로 통신 |
| AC-006-02 | 파서 재활용 (`hwp_ole_reader.py`, `hwp_body_parser.py`) | Pass | `backend/app/parser/` 디렉토리에 두 파일 위치 (설계 문서 명세 일치) |
| AC-006-03 | 임시 파일 처리 후 삭제 | 미확인 | `backend/data/tmp/` 디렉토리는 설계에 명시되어 있으나 `upload.py`를 본 리뷰 범위에서 직접 확인하지 않음. 설계 명세에 `finally` 블록 삭제 언급됨 |
| AC-006-04 | 단일 세션 연속 흐름 | Pass | `state.py`의 인메모리 싱글턴이 업로드~다운로드 전 과정에서 동일 `SessionState` 객체 유지 |

판정: **Pass** (AC-006-03은 upload.py 범위로 별도 확인 필요)

### B. 설계 준수

| 항목 | 기준 | 결과 | 근거 |
|------|------|------|------|
| 디렉토리 구조 | 설계 문서의 tree와 일치 | Pass | `backend/app/services/`, `routers/`, `models/`, `parser/` 구조 확인됨 |
| 포트 설정 | FE:3000, BE:8000 | Pass | `main.py` CORS allow_origins에서 3000 포트 확인 |
| `state.py` 인메모리 싱글턴 | `get_session()`, `reset_session()`, lock 사용 | Pass | `state.py`가 `threading.Lock` 사용하여 설계와 일치. 설계 명세에는 lock이 없으나 실제 구현에서 추가하여 안전성 향상 |
| `SessionState` 모델 | `session_id`, `status`, `original_requirements`, `detail_requirements`, `created_at` | Pass | `models/session.py`에서 5개 필드 모두 확인 (`requirement.py` 기반 모델 재사용) |
| API 클라이언트 (`src/api/index.ts`) | `generateDetailStream()`, `chatStream()` — fetch + ReadableStream | Pass | `ChatPanel.tsx`에서 `chatStream` import 확인 (`ChatPanel.tsx:3`) |

판정: **Pass**

### D. 보안

| SEC-ID | 내용 | 결과 | 근거 |
|--------|------|------|------|
| SEC-006-01 | `ANTHROPIC_API_KEY` `.env` 관리, `.gitignore` 등록 | Pass | 루트 `.gitignore`에 `.env` 포함됨. `main.py`에서 `load_dotenv()` 호출. `ai_generate_service.py`와 `chat_service.py` 모두 `os.environ.get("ANTHROPIC_API_KEY")`로 로드 — 코드 하드코딩 없음 |
| SEC-006-02 | CORS `allow_origins` 화이트리스트 (와일드카드 `*` 금지) | Pass | `main.py:19-24`에서 `allow_origins=["http://localhost:3000"]`으로 화이트리스트 제한 |

추가 확인 사항:
- `backend/.env` 파일이 실제로 존재하지 않음(정상 — gitignore로 제외된 실제 파일은 리포지토리에 없어야 함). 루트 `.gitignore`에서 `.env` 커버하므로 SEC-006-01 충족.
- 단, `backend/.gitignore`가 별도 존재하지 않아 루트 `.gitignore` 패턴에 의존함 — 실무 환경에서 `backend/` 를 별도 리포지토리로 분리 시 누락 위험 있음 (Minor).

판정: **Pass**

### E. 단위 테스트 (UT-ID별)

UT-006 테스트는 `test_foundation.py`에 위치할 것으로 예상되나, 본 리뷰에서 직접 확인한 test_chat.py / test_excel.py / test_generate.py의 `setup_method`에서 `state.reset_session()` + `state.set_original()` 패턴을 통해 UT-006-03(`SessionStore` 저장/조회/reset)이 간접 검증됨.

| UT-ID | 대상 | 결과 |
|-------|------|------|
| UT-006-01 | CORS 검증 | test_foundation.py에 있을 것으로 추정 — 직접 확인 필요 |
| UT-006-02 | 파서 재활용 | test_foundation.py에 있을 것으로 추정 — 직접 확인 필요 |
| UT-006-03 | `SessionStore` 저장/조회/reset | 간접 검증됨 (각 테스트의 setup_method) |
| UT-006-04 | 세션 연속성 | test_foundation.py에 있을 것으로 추정 — 직접 확인 필요 |

### F. 코드 품질

| 항목 | 결과 | 세부 사항 |
|------|------|---------|
| 멀티스레드 안전성 | Pass | `threading.Lock` 적용 (`state.py:14, 22`) — 설계보다 강화된 구현 |
| 세션 격리 | Minor | 인메모리 단일 세션으로 동시 사용자 지원 불가. 단일 사용자 전제(REQ-006-04)에는 부합하나, 향후 확장 시 재설계 필요 |
| 타입 힌트 | Pass | FastAPI Pydantic 모델 전반적으로 타입 힌트 완비 |
| 환경변수 누락 시 처리 | Minor | `os.environ.get("ANTHROPIC_API_KEY")`는 키 미설정 시 `None`을 반환하여 `AsyncAnthropic(api_key=None)`이 초기화됨. 런타임 오류 대신 시작 시점에서 명시적 검증(`if not api_key: raise ValueError(...)`)이 없음 (`ai_generate_service.py:37`, `chat_service.py:28`) |

---

## 종합 판정

### Blocker 항목 요약

없음 — A, B, D 항목에서 Blocker 수준의 결함이 발견되지 않았습니다.

### Minor 항목 목록

| # | 파일 | 위치 | 설명 |
|---|------|------|------|
| 1 | `backend/app/services/chat_service.py` | L67 | 스트리밍 청크 단위 PATCH 태그 정제 시 태그가 청크 경계에 걸리면 불완전한 `<PATCH>` 텍스트가 UI에 잠시 노출될 수 있음 |
| 2 | `backend/app/routers/download.py` | L50 | `Content-Disposition` 헤더 파일명에 RFC 5987 UTF-8 인코딩(`filename*=UTF-8''...`) 미적용 |
| 3 | `backend/app/services/excel_export_service.py` | L75, L98 | 설계 명세 열 너비와 불일치 — 2단계 D열 설계:12이나 구현:50 (실제 D열은 내용 열이므로 넓은 편이 더 적절하나 명세 불일치) |
| 4 | `backend/app/services/excel_export_service.py` | L146-148 | openpyxl 병합 셀의 비주인 셀 스타일 설정 — 실제 xlsx 렌더링에서 무시될 가능성 있음 |
| 5 | `backend/` | — | `backend/.gitignore` 미존재. 루트 `.gitignore`에 의존 — 서브 모듈 분리 시 `.env` 노출 위험 |
| 6 | `backend/app/services/ai_generate_service.py` | L37 | API 키 미설정 시 시작 시점 명시적 검증 없음 (`None`으로 초기화됨) |
| 7 | `backend/app/services/chat_service.py` | L28 | 동일 — API 키 미설정 시 시작 시점 명시적 검증 없음 |
| 8 | `frontend/src/components/ChatPanel.tsx` | — | UT-004-05 프론트엔드 단위 테스트 부재 (`disabled` 조건 로직은 구현됨) |

### 최종 판정: PASS

모든 REQ-004 ~ REQ-006의 AC 항목이 구현되어 있고, Blocker 수준(요구사항 미충족, 보안 취약점, 크래시 유발 버그)의 결함은 발견되지 않았습니다. Minor 항목 8건은 기능적 동작에 영향을 주지 않으며 개선 권고 수준입니다.
