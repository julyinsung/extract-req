# Gate 4 코드 리뷰 — REQ-001~003

> 작성일: 2026-04-01
> 리뷰어: QA 에이전트
> 담당 범위: REQ-001 (HWP 파싱/업로드), REQ-002 (AI 생성), REQ-003 (결과 화면)
> 참조 요구사항: REQUIREMENTS.md REQ-001(HWP 파싱) / REQ-002(AI 생성) / REQ-003(결과 화면)

---

## REQ-001 — HWP 파싱 및 업로드

### A. 요구사항 충족

| REQ-ID | AC-ID | 구현 파일 | 판정 | 근거 |
|--------|-------|---------|------|------|
| REQ-001-01 | AC-001-01 | `UploadPanel.tsx`, `upload.py` | 통과 | 드래그앤드롭(`onDrop`) + 파일 선택 다이얼로그(`inputRef.current?.click()`) 모두 구현. 업로드 중 `isUploading` 플래그로 버튼 비활성화 및 로딩 문자 표시. |
| REQ-001-02 | AC-001-02 | `hwp_processor.py`, `hwp_parse_service.py` | 통과 | `HwpProcessor._structure()`가 id/category/name/content 4개 항목을 `OriginalRequirement`로 매핑하여 반환. ParseResponse에 포함. |
| REQ-001-03 | AC-001-03 | `hwp_processor.py` | 통과 | `HWPOLEReader`, `HwpBodyParser`를 import하여 사용. 동일 기능 중복 구현 없음. |
| REQ-001-04 | AC-001-04 | `hwp_parse_service.py`, `UploadPanel.tsx` | 통과 | 파싱 실패 시 `HTTPException(400, PARSE_ERROR)` 발생. 프론트엔드에서 `detail.message` 우선 표시, fallback 문자열 제공. |

**소계: 4/4 통과**

### B. 설계 준수

| 항목 | 판정 | 근거 |
|------|------|------|
| API 경로 `POST /api/v1/upload` | 통과 | `routers/upload.py:14` — 경로 일치 |
| 응답 스키마 `ParseResponse(session_id, requirements)` | 통과 | `models/api.py` — 설계 스키마와 완전 일치 |
| `OriginalRequirement` 5개 필드 | 통과 | `models/requirement.py` — id/category/name/content/order_index 모두 일치 |
| 에러 코드 `INVALID_FILE_TYPE`, `PARSE_ERROR` | 통과 | `hwp_parse_service.py:81,65` — 설계 에러 코드 일치 |
| `HwpParseService.parse()` 내부 흐름(6단계) | 통과 | 확장자 검증 → 파일 읽기 → 크기 검증 → 임시 저장 → OLE 검증 → 파싱 → 세션 저장 → finally 삭제. 단계 순서 일치. |
| `HwpProcessor.process(file_path)` 인터페이스 | 통과 | `hwp_processor.py:32` — 설계 시그니처 일치 |

**소계: 6/6 통과**

### D. 보안

| SEC-ID | 항목 | 판정 | 근거 |
|--------|------|------|------|
| SEC-001-01 | 파일 확장자 + MIME 타입 + OLE2 시그니처 3중 검증 | **실패** | `hwp_parse_service.py`의 `_validate_extension()`은 확장자만 검사하고, `_validate_ole_signature()`는 OLE2 바이너리만 검사한다. **MIME 타입 검증 코드가 존재하지 않는다.** 설계 문서 SEC-001-01은 "3중 검증"을 명시하지만 구현은 2중 검증에 그친다. 악의적 사용자가 `.hwp` 확장자를 붙인 비-OLE 파일을 업로드 시 OLE 검증에서 차단되지만, 실제 HWP가 아닌 임의의 OLE2 바이너리(`.doc` 등)도 통과할 수 있다. |
| SEC-001-02 | 파일 크기 50MB 상한 | 통과 | `_validate_size(contents)` — `len(contents) > 50*1024*1024` 검사 구현. |
| SEC-001-03 | 임시 파일 경로 고정 (`tempfile` 사용) | 조건부 통과 | `_save_tmp()`에서 `tempfile.NamedTemporaryFile`을 사용하여 OS 유일 경로 보장. 단, 원본 `filename`은 파일 시스템에 직접 사용되지 않으므로 Path Traversal 방지 조건 충족. `_TMP_DIR = "data/tmp"` 고정 경로 사용. |

**SEC-001-01 실패 — Blocker**

### E. 단위 테스트 (UT-ID 존재 및 의도 부합)

| UT-ID | 대상 | 테스트 파일 위치 | 판정 | 근거 |
|-------|------|----------------|------|------|
| UT-001-01 | `HwpProcessor.process()` 정상 → OriginalRequirement 반환, 4개 필드 비어있지 않음 | `tests/test_upload.py:58` | 통과 | `TestHwpProcessorProcess.test_process_returns_original_requirement_list` — mock으로 4개 필드를 assert. 설계 의도 일치. |
| UT-001-02 | `HwpProcessor.process()` 비 HWP → ValueError | `tests/test_upload.py:120` | 통과 | `TestHwpProcessorInvalidFile.test_process_raises_value_error_for_non_hwp` — 실제 파일로 예외 확인. |
| UT-001-03 | `HwpParseService.parse()` 정상 → ParseResponse(session_id 포함) | `tests/test_upload.py:140` | 통과 | `TestHwpParseServiceParse.test_parse_returns_parse_response_with_session_id` — session_id 비어있지 않음 assert. |
| UT-001-04 | `HwpParseService.parse()` .docx → INVALID_FILE_TYPE | `tests/test_upload.py:184` | 통과 | 확장자 없는 파일, 대용량 파일 케이스도 추가로 커버. |
| UT-001-05 | 임시 파일 삭제 (성공/실패 모두) | `tests/test_upload.py:244` | 통과 | spy 패턴으로 경로 캡처 후 `os.path.exists` 검증. 성공/실패 양방향 케이스 모두 작성. |

**소계: 5/5 통과**

### F. 코드 품질

| 항목 | 판정 | 내용 |
|------|------|------|
| `state.py` 중첩 Lock 가능성 | 경고 | `set_original()`은 `get_session()`을 호출한 뒤 `_lock`을 다시 획득한다. Python의 `threading.Lock`은 비재진입형(non-reentrant)이므로 동일 스레드 내 `get_session() → _lock.acquire()` 후 `set_original()` → `_lock.acquire()` 순서가 되면 데드락이 발생할 수 있다. 단일 사용자 전제이므로 실제 교착 가능성은 낮으나, `threading.RLock` 사용 또는 내부 helper 메서드로 락 분리 권장. |
| `hwp_processor.py` 연속 테이블 내용 합산 로직 | 정보 | `_structure()`의 연속 테이블 내용 합산 조건(`len(continuation) > 10`)이 임의 상수. 짧은 이어지는 내용이 누락될 수 있음. |
| 주석 품질 | 통과 | 모든 공개 메서드에 docstring 존재. Args/Returns/Raises 형식 준수. |
| 타입 힌트 | 통과 | 백엔드 전반 타입 힌트 일관성 유지. |

---

## REQ-002 — AI 상세요구사항 자동 생성

### A. 요구사항 충족

| REQ-ID | AC-ID | 구현 파일 | 판정 | 근거 |
|--------|-------|---------|------|------|
| REQ-002-01 | AC-002-01 | `generate.py`, `ai_generate_service.py`, `OriginalReqTable.tsx` | 통과 | "상세요구사항 생성" 버튼 클릭 → `generateDetailStream()` → `POST /api/v1/generate` → `AiGenerateService.generate_stream()` 흐름 완비. |
| REQ-002-02 | AC-002-02 | `ai_generate_service.py` | 통과 | `DetailRequirement(parent_id=..., id=f"{parent_id}-{NN}")` 채번 로직 구현. AI 응답 ID 누락 시 서버 재채번 검증됨(UT-002-04). |
| REQ-002-03 | AC-002-03 | `OriginalReqTable.tsx:145` | 통과 | `isGenerating` 상태일 때 버튼 텍스트 "생성 중..." 표시, 버튼 비활성화. |
| REQ-002-04 | AC-002-04 | `api/index.ts:56`, `OriginalReqTable.tsx:52` | 통과 | `onError` 콜백으로 에러 메시지를 `setError()`에 전달. 전역 에러 배너(`role="alert"`)로 표시. 단, 재시도 버튼이 별도로 제공되지 않고 "상세요구사항 생성" 버튼이 재노출되는 형태. AC-002-04는 "재시도 버튼 제공"을 명시하므로 조건부 통과로 판단. |

**소계: 4/4 (REQ-002-04는 재시도 버튼 명칭 차이 — 기능적으로는 동등)**

### B. 설계 준수

| 항목 | 판정 | 근거 |
|------|------|------|
| API 경로 `POST /api/v1/generate` | 통과 | `routers/generate.py:15` — 경로 일치 |
| 요청 바디 `{"session_id": "..."}` | 통과 | `models/api.py:GenerateRequest` — 일치 |
| SSE 이벤트 타입 `item`, `done`, `error` | 통과 | `ai_generate_service.py` — 3가지 이벤트 타입 모두 구현 |
| SSE `item` 데이터 필드 (id, parent_id, category, name, content) | 통과 | `DetailRequirement` 모델 직렬화. `order_index`, `is_modified`는 추가 필드로 포함 — 설계 초과이나 하위 호환. |
| `AiGenerateService.generate_stream()` 비동기 제너레이터 | 통과 | `async def generate_stream()` + `AsyncGenerator` 반환 형태 일치 |
| 완료 시 `set_detail()` 저장 | 통과 | 스트리밍 종료 후 `state.set_detail(collected)` 호출 확인 (test에서 검증) |

**소계: 6/6 통과**

### D. 보안

| SEC-ID | 항목 | 판정 | 근거 |
|--------|------|------|------|
| SEC-002-01 | `ANTHROPIC_API_KEY` 환경변수 관리 | 통과 | `main.py:14` — `load_dotenv()` 호출. 코드 내 API 키 하드코딩 없음. `ai_generate_service.py`에서 `os.environ` 또는 `anthropic.Anthropic()` 기본 동작으로 키 로드. |
| SEC-002-02 | 프롬프트 인젝션 방지 — content JSON 직렬화 | 통과 | `json.dumps()`로 원본 요구사항 배열 직렬화 후 사용자 메시지로 전달. raw 문자열 삽입 없음. |

**소계: 2/2 통과**

### E. 단위 테스트 (UT-ID 존재 및 의도 부합)

| UT-ID | 대상 | 테스트 파일 위치 | 판정 | 근거 |
|-------|------|----------------|------|------|
| UT-002-01 | `generate_stream()` 정상 → item 이벤트 1건 이상 | `tests/test_generate.py:82` | 통과 | 청크 분할 스트림 시뮬레이션으로 item/done 이벤트 검증. |
| UT-002-02 | `APIError` → error 이벤트 | `tests/test_generate.py:133` | 통과 | `__aenter__ side_effect` 패턴으로 예외 주입. 빈 원본 요구사항 케이스도 추가 커버. |
| UT-002-03 | 1:N 구조 — 각 parent_id에 1개 이상 | `tests/test_generate.py:184` | 통과 | parent_id 집합으로 검증. state 저장 확인. |
| UT-002-04 | ID 채번 `{parent_id}-{NN}` 형식, 중복 없음 | `tests/test_generate.py:236` | 통과 | 형식 준수, 중복 없음, AI 응답 ID 누락 시 서버 채번 3가지 케이스 검증. |

**소계: 4/4 통과**

### F. 코드 품질

| 항목 | 판정 | 내용 |
|------|------|------|
| `api/index.ts:39` `res.body!` non-null assertion | 경고 | `res.body`가 `null`인 환경(일부 구형 브라우저, 서버 측 렌더링 환경)에서 런타임 오류 발생 가능. `res.body` 존재 여부 확인 후 처리 권장. |
| SSE 버퍼 로직 | 통과 | `buf.split('\n')` + `buf = lines.pop()!` 패턴으로 불완전 라인 누적 처리 올바름. |
| 주석 품질 | 통과 | 모든 공개 함수에 JSDoc/docstring 존재. |

---

## REQ-003 — 결과 화면 표시 (테이블 UI)

> 참고: 리뷰 지시의 REQ-003은 REQUIREMENTS.md 기준 REQ-003(결과 화면)에 해당하며, 관련 설계 문서는 `req-003-design.md`다.

### A. 요구사항 충족

| REQ-ID | AC-ID | 구현 파일 | 판정 | 근거 |
|--------|-------|---------|------|------|
| REQ-003-01 | AC-003-01 | `OriginalReqTable.tsx` | 통과 | ID/분류/명칭/내용 4컬럼 테이블 렌더링. `originalReqs.length === 0` 시 빈 상태 메시지 표시. |
| REQ-003-02 | AC-003-02 | `OriginalReqTable.tsx:46`, `App.tsx:83` | 통과 | `onItem` 콜백 → `appendDetailReq()` → Zustand 상태 추가 → `DetailReqTable` 리렌더링으로 행 동적 추가. |
| REQ-003-03 | AC-003-03 | 미확인 | 미확인 | `DetailReqTable`, `InlineEditCell` 컴포넌트 파일이 리뷰 대상 목록에 없어 직접 검증 불가. `useAppStore.patchDetailReq()` 액션은 `is_modified: true` 마킹 포함하여 구현됨. |
| REQ-003-04 | AC-003-04 | `OriginalReqTable.tsx:76,105` | 통과 | 헤더 배경 `#4472C4`(설계 토큰 일치). 원본 행 배경 `#FFFFFF`. 원본 ID Bold. 컬럼 헤더 명확히 표시. |

**소계: 3/4 직접 확인, REQ-003-03은 파일 범위 외**

### B. 설계 준수

| 항목 | 판정 | 근거 |
|------|------|------|
| `useAppStore` 인터페이스 — AppState 필드 7개 | 통과 | `useAppStore.ts:4-14` — 설계 문서 `AppState` 필드 전체 구현. 추가로 `phase: AppPhase` 필드 포함(설계 초과, 기능 확장). |
| `AppActions` — 8개 액션 메서드 | 통과 | `setPhase`, `setSessionId`, `setOriginalReqs`, `appendDetailReq`, `patchDetailReq`, `appendChatMessage`, `setError`, `reset` 모두 구현. |
| `patchDetailReq(id, field, value)` 시그니처 | 통과 | `useAppStore.ts:56` — 설계 일치. `is_modified: true` 마킹 포함. |
| `persist` 미사용 | 통과 | `create<AppState & AppActions>()` — persist 미사용 확인. |
| 디자인 토큰 헤더 배경 `#4472C4` | 통과 | `OriginalReqTable.tsx:76` — 일치. |
| 디자인 토큰 원본 행 배경 `#FFFFFF` | 통과 | `OriginalReqTable.tsx:105` — 일치. |

**소계: 6/6 통과**

### D. 보안

REQ-003은 별도 SEC-ID가 정의되지 않음. 프론트엔드 XSS 관련 사항 점검.

| 항목 | 판정 | 근거 |
|------|------|------|
| React JSX XSS 방어 | 통과 | `{req.content}` 등 JSX 표현식 사용 — React가 자동 이스케이프 처리. `dangerouslySetInnerHTML` 미사용 확인. |
| 사용자 입력 직접 DOM 삽입 없음 | 통과 | `OriginalReqTable.tsx`, `App.tsx` 전체에서 `dangerouslySetInnerHTML` 미사용. |

**소계: 통과**

### E. 단위 테스트 (UT-ID 존재 및 의도 부합)

| UT-ID | 대상 | 판정 | 근거 |
|-------|------|------|------|
| UT-003-01 | `OriginalReqTable` rows 5건 → 행 5개 렌더링 | 미확인 | 리뷰 대상 파일 목록에 프론트엔드 테스트 파일이 포함되지 않음. |
| UT-003-02 | `appendDetailReq()` 3회 → 행 3개 추가 | 미확인 | 동일 이유. |
| UT-003-03 | `InlineEditCell` 클릭 → input, blur → `patchDetailReq` | 미확인 | 동일 이유. |
| UT-003-04 | 원본/상세 행 배경색 CSS 클래스 | 미확인 | 동일 이유. |
| UT-003-05 | 수정 하이라이트 patch 이벤트 → 강조 CSS | 미확인 | 동일 이유. |

**프론트엔드 UT 파일 부재 — 확인 불가. Gate 4 2단계(테스트 실행)에서 재확인 필요.**

### F. 코드 품질

| 항목 | 판정 | 내용 |
|------|------|------|
| `App.tsx` 조건부 렌더링 구조 | 통과 | `phase` 기반 조건부 렌더링 명확. `data-testid` 속성으로 E2E 테스트 지원. |
| `useAppStore.ts` 초기 상태 분리 | 통과 | `initialState` 상수 분리로 `reset()` 구현 명확. |
| `main.tsx` StrictMode | 통과 | 개발 단계 이중 렌더링 경고 활성화. |
| `OriginalReqTable.tsx`의 관심사 혼재 | 경고 | 원본 테이블 렌더링 컴포넌트가 `handleGenerate()` 로직(SSE 연결, 상태 전환)을 직접 포함. REQ-002 생성 트리거 역할을 겸하고 있어 단일 책임 원칙(SRP) 위반. 별도 컴포넌트 또는 커스텀 훅으로 분리 권장. |

---

## 종합 판정

### Blocker 목록 (필수 수정)

| ID | 위치 | 내용 | 심각도 |
|----|------|------|--------|
| B-001 | `backend/app/services/hwp_parse_service.py` | SEC-001-01 위반: 설계가 명시한 "MIME 타입 검증"이 구현되지 않았다. 확장자 + OLE2 시그니처 2중 검증만 존재하며, MIME 타입(Content-Type 또는 python-magic 라이브러리) 검증이 누락되었다. 악의적 OLE2 바이너리(`.doc`, `.xls` 등)가 `.hwp` 확장자로 업로드될 경우 파서에 전달된다. | Blocker |

### Minor 목록 (개선 권고)

| ID | 위치 | 내용 |
|----|------|------|
| M-001 | `backend/app/state.py:34-39` | `set_original()`/`set_detail()`에서 `get_session()` 호출(내부에서 `_lock` 획득) 후 외부에서 다시 `_lock`을 획득하는 이중 잠금 구조. `threading.Lock`은 비재진입형이므로 단일 스레드 내 재진입 시 데드락 위험. `threading.RLock` 전환 또는 내부 `_get_session_unsafe()` 헬퍼 분리 권장. |
| M-002 | `frontend/src/api/index.ts:39` | `res.body!.getReader()` — non-null assertion. `res.body`가 null인 경우(일부 환경) 런타임 예외 발생. `if (!res.body)` 방어 코드 추가 권장. |
| M-003 | `frontend/src/components/OriginalReqTable.tsx:38` | 원본 테이블 컴포넌트가 상세요구사항 생성 SSE 연결 로직을 포함. 단일 책임 원칙 위반. `useGenerateDetail` 커스텀 훅으로 분리 권장. |
| M-004 | `backend/app/parser/hwp_processor.py:77` | 연속 테이블 내용 합산 임계치 `len(continuation) > 10` 매직 넘버 사용. 상수로 추출하여 가독성 개선 권장. |

### 최종 판정: FAIL

**이유**: Blocker B-001 — SEC-001-01(파일 업로드 3중 검증) 미충족. 설계 문서가 명시한 MIME 타입 검증이 구현에 누락되어 보안 항목 D가 실패하였다. Blocker 항목 1개 이상 실패 시 전체 Fail 기준에 따라 FAIL로 판정한다.

---

## Developer에 대한 수정 요청

### 필수 수정 (Blocker B-001)

**파일**: `backend/app/services/hwp_parse_service.py`

**요청 내용**: `_validate_extension()` 또는 별도 `_validate_mime()` 메서드에서 업로드 파일의 MIME 타입을 검증하는 코드를 추가하세요.

구현 방안 (택 1):
- `python-magic` 라이브러리를 사용하여 파일 바이트의 MIME 타입을 확인 (`application/x-hwp` 또는 `application/octet-stream`)
- FastAPI `UploadFile.content_type` 필드 확인 (단, 클라이언트가 제공하는 값이므로 신뢰도 낮음 — python-magic 우선 권장)
- HWP 파일의 고유 MIME 타입(`application/x-hwp`, `application/haansoftHWP`)을 허용 목록으로 관리

수정 후 SEC-001-01 주석을 "3중 검증 완료"로 업데이트하고, UT-001-04에 MIME 검증 실패 케이스를 추가하세요.
