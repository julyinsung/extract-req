# REQ-004 / REQ-009 설계 문서 (추가 변경분)

> Gate 2 — Architect 작성
> 담당 범위: REQ-004-04, REQ-004-05, REQ-004-06 (신규), REQ-009-01(수정), REQ-009-04(신규)

---

## 개요

- **REQ 그룹**: REQ-004 — 채팅 기반 AI 수정 (그룹 컨텍스트 전환) / REQ-009 — 세션 그룹별 독립 관리
- **설계 방식**: 최소 변경 증분 패치 (기존 PATCH 흐름 보존, 신규 REPLACE 흐름 추가)
- **핵심 결정사항**:
  - REQ-004: 채팅 요청에 `req_group` 필드를 추가하여 서버가 해당 그룹의 원본+상세 항목만 컨텍스트로 사용한다. REPLACE 이벤트는 PATCH와 별개 태그(`<REPLACE>`)로 구분하며 기존 PATCH 흐름은 변경 없다.
  - REQ-009: 단일 `sdk_session_id` 필드를 `Dict[str, str]` 구조로 교체한다. 이 변경은 `state.py`와 `session.py`에 국한되며 라우터 인터페이스는 변경 없다. 단, `ChatRequest`와 `GenerateRequest`에 `req_group` 필드가 추가됨으로써 세션 키 조회가 가능해진다.

---

## 영향도 분석

기존 구현 파일을 직접 확인하여 수정 범위를 파악했다.

### 1. 채팅 프롬프트 구성 방식 (REQ-004-05 영향)

`chat_service.py`의 `_build_system_prompt(details: list)` 함수는 현재 전체 상세항목을 받아 시스템 프롬프트에 JSON으로 직렬화한다. REQ-004-05는 "선택된 REQ 그룹의 원본 텍스트 + 해당 그룹 상세항목만 전달"을 요구하므로, 함수 시그니처를 변경해야 한다.

`chat_service_sdk.py`는 `chat_service.py`에서 `_build_system_prompt`를 직접 import하므로 시그니처 변경 시 두 파일이 동시에 영향을 받는다. 단, `chat_service_sdk.py` 코드 수정은 최소화하며 시그니처 변경에 따른 인자 전달만 조정한다.

### 2. `sdk_session_id` 단일 필드 → Dict 변경 시 수정 파일

| 파일 | 변경 내용 |
|------|---------|
| `backend/app/models/session.py` | `sdk_session_id: str | None` 필드 제거, `sdk_sessions: Dict[str, str]` 필드 추가 |
| `backend/app/state.py` | `get_sdk_session_id()`, `set_sdk_session_id()` 시그니처에 `req_group: str` 파라미터 추가 |
| `backend/app/services/ai_generate_service_sdk.py` | `state.set_sdk_session_id(sdk_sid)` → `state.set_sdk_session_id(req_group, sdk_sid)` |
| `backend/app/services/chat_service_sdk.py` | `state.get_sdk_session_id()` → `state.get_sdk_session_id(req_group)` |
| `backend/app/models/api.py` | `ChatRequest`에 `req_group: str` 추가, `GenerateRequest`에 `req_group: str` 추가 |

프론트엔드는 `req_group` 값을 chat/generate 요청 바디에 포함하여 전송해야 한다.

### 3. 기존 PATCH 이벤트 처리 흐름과 REPLACE 추가 시 충돌 여부

`chat_service.py`의 PATCH 처리 흐름은 `<PATCH>` 태그를 정규식으로 감지하여 일괄 처리한다. REPLACE는 `<REPLACE>` 태그를 별도 정규식으로 처리한다. 두 태그는 독립적이므로 충돌이 없다.

단, `_process_patches()` 함수는 PATCH 전용이다. REPLACE 처리 함수 `_process_replace()`를 별도로 추가하고, 스트리밍 완료 후 PATCH → REPLACE 순으로 실행한다. `chat_service_sdk.py`도 동일하게 `_process_patches`, `_process_replace`를 순서대로 호출한다.

---

## 변경 대상 파일 목록

### REQ-004

| 파일 경로 | 변경 유형 | 변경 내용 요약 |
|----------|----------|--------------|
| `backend/app/models/api.py` | 수정 | `ChatRequest`에 `req_group: str` 추가 |
| `backend/app/services/chat_service.py` | 수정 | `_build_system_prompt` 시그니처 변경, `_process_replace()` 함수 추가, REPLACE SSE 이벤트 발행 |
| `backend/app/services/chat_service_sdk.py` | 수정 | `_build_system_prompt` 호출 시 변경된 인자 전달, `_process_replace` 호출 추가 |
| `frontend/src/store/useAppStore.ts` | 수정 | `selectedReqGroup: string | null` 상태 및 `setSelectedReqGroup` 액션 추가, `replaceDetailReqGroup` 액션 추가 |
| `frontend/src/components/ChatPanel.tsx` | 수정 | 헤더에 선택된 그룹 표시, `req_group` 포함 전송, `onReplace` 이벤트 처리 |
| `frontend/src/api/index.ts` | 수정 | `chatStream` 콜백에 `onReplace` 추가, 페이로드에 `req_group` 포함 |

### 불변 파일 (REQ-004)

| 파일 경로 | 이유 |
|----------|------|
| `backend/app/routers/chat.py` | 라우터 인터페이스(`ChatRequest` 바디 수신) 변경 없음. `req_group` 필드는 모델에서 추가됨 |
| `backend/app/models/session.py` | REQ-004만으로는 세션 구조 변경 없음 (REQ-009 변경에 포함) |

### REQ-009

| 파일 경로 | 변경 유형 | 변경 내용 요약 |
|----------|----------|--------------|
| `backend/app/models/api.py` | 수정 | `GenerateRequest`에 `req_group: str` 추가 (ChatRequest와 동일 변경이지만 목적이 다름) |
| `backend/app/models/session.py` | 수정 | `sdk_session_id: str | None` 제거, `sdk_sessions: Dict[str, str]` 필드 추가 |
| `backend/app/state.py` | 수정 | `get_sdk_session_id(req_group)`, `set_sdk_session_id(req_group, session_id)` 시그니처 변경 |
| `backend/app/services/ai_generate_service_sdk.py` | 수정 | `generate_stream(session_id, req_group)` 파라미터 추가, 저장 시 그룹 키 사용 |
| `backend/app/routers/generate.py` | 수정 | `service.generate_stream(req.session_id, req.req_group)` 호출로 변경 |
| `frontend/src/api/index.ts` | 수정 | `generateDetailStream` 페이로드에 `req_group` 포함 |

### 불변 파일 (REQ-009)

| 파일 경로 | 이유 |
|----------|------|
| `backend/app/services/ai_generate_service.py` | anthropic_api 경로 — 세션 기능 해당 없음 |
| `backend/app/services/chat_service.py` | REQ-009는 SDK 경로 전용. anthropic_api 경로의 ChatService는 세션을 관리하지 않음 |
| `backend/app/routers/chat.py` | `req_group` 필드는 `ChatRequest` 모델에서 처리되므로 라우터 코드 변경 불필요 |

---

## 시스템 구조

### REQ-004: 그룹 컨텍스트 채팅 흐름

```
[사용자가 원본 요구사항 테이블에서 REQ-001 행 클릭]
  → useAppStore.setSelectedReqGroup("REQ-001")
      → ChatPanel 헤더: "REQ-001 컨텍스트로 대화 중" 표시
      → chatHistory 초기화 여부: 그룹 전환 시 초기화 (REQ-004-04 명시 없음 — 유지로 가정)

[채팅 메시지 전송]
  ChatPanel.handleSend()
    → req_group = selectedReqGroup  ("REQ-001")
    → chatStream({ session_id, message, history, req_group }, callbacks)
        → POST /api/v1/chat { session_id, message, history, req_group: "REQ-001" }
            → chat 라우터
                → ChatService / ChatServiceSDK.chat_stream(session_id, message, history, req_group)
                    → state.get_original_by_group(req_group) — REQ-001 원본 1건 조회
                    → state.get_detail_by_group(req_group)  — REQ-001 상세항목만 조회
                    → _build_system_prompt(original_req, filtered_details) 호출
                    → Claude 스트리밍 응답 처리
                        → <PATCH> 감지 → patch SSE 이벤트
                        → <REPLACE> 감지 → replace SSE 이벤트
                        → 나머지 텍스트 → text SSE 이벤트
                    → done SSE 이벤트

[SSE 이벤트 수신 — ChatPanel]
  onText  → streamingText 갱신
  onPatch → patchDetailReq(id, field, value) + req-highlight 이벤트
  onReplace → replaceDetailReqGroup(req_group, items) + req-group-replace 이벤트
  onDone  → 스트리밍 완료 처리
```

### REQ-009: 그룹별 독립 세션 흐름

```
[REQ-001 최초 생성]
  POST /api/v1/generate { session_id, req_group: "REQ-001" }
    → AIGenerateServiceSDK.generate_stream(session_id, "REQ-001")
        → ResultMessage.session_id 추출
        → state.set_sdk_session_id("REQ-001", session_id)
            → sdk_sessions["REQ-001"] = "sess-abc"

[REQ-002 최초 생성 (REQ-001과 독립)]
  POST /api/v1/generate { session_id, req_group: "REQ-002" }
    → ResultMessage.session_id 추출
    → state.set_sdk_session_id("REQ-002", session_id)
        → sdk_sessions["REQ-002"] = "sess-xyz"

[REQ-001 컨텍스트 채팅]
  POST /api/v1/chat { ..., req_group: "REQ-001" }
    → state.get_sdk_session_id("REQ-001") → "sess-abc"
    → ClaudeAgentOptions(resume="sess-abc")
    → REQ-002의 "sess-xyz"는 변경 없음 (AC-009-04)

[새 HWP 업로드 또는 재생성]
  → state.reset_session()
      → SessionState() 새로 생성: sdk_sessions = {}
      → 모든 그룹 세션 초기화 (AC-009-03)
```

---

## 모듈/컴포넌트 설계

### REQ-004

#### `backend/app/models/api.py` 변경

- **책임**: `ChatRequest`에 현재 선택된 REQ 그룹 정보를 추가한다.
- **인터페이스**:
  ```
  ChatRequest:
    기존 필드 유지 (session_id, message, history)
    + req_group: str  — 선택된 REQ 그룹 ID (예: "REQ-001")
  ```
- **제약**: `req_group`은 서버가 컨텍스트 필터링에 사용한다. 빈 문자열이 전달되면 서버는 "전체 컨텍스트"로 처리할 수 있으나, 기존 동작(전체 상세항목 전달)과 동일해지므로 REQ-004-05 위반이다. Pydantic `min_length=1` 제약으로 빈 값을 차단한다.
- **결정 근거**: 기존 `session_id`는 서버 state 조회 키로만 사용하고 있어 그룹 정보를 담지 않는다. 별도 필드로 분리하여 단일 책임을 유지한다.

#### `backend/app/services/chat_service.py` 변경

- **책임**: 채팅 컨텍스트를 선택된 REQ 그룹으로 제한하고, REPLACE 태그를 처리한다.
- **변경 인터페이스**:
  ```python
  # 기존
  async def chat_stream(session_id, message, history) -> AsyncGenerator[str, None]

  # 변경 후
  async def chat_stream(session_id, message, history, req_group: str) -> AsyncGenerator[str, None]
  ```
  ```python
  # 기존
  def _build_system_prompt(details: list) -> str

  # 변경 후
  def _build_system_prompt(original_req: OriginalRequirement | None, filtered_details: list) -> str
  ```
  ```python
  # 신규 추가
  def _process_replace(full_text: str, req_group: str) -> tuple[list, list[str]]
  # 반환: (교체될 DetailRequirement 목록, SSE 이벤트 문자열 목록)
  ```
- **시스템 프롬프트 변경 내용**: 기존 전체 상세항목 JSON 대신, 원본 요구사항 1건의 텍스트와 해당 그룹의 상세항목만 포함한다. REPLACE 태그 사용법을 프롬프트에 추가한다.
- **REPLACE 태그 프로토콜**:
  ```
  <REPLACE>[
    {"name":"...", "content":"...", "category":"..."},
    {"name":"...", "content":"...", "category":"..."}
  ]</REPLACE>
  ```
  - REPLACE 태그 내부: 해당 그룹 상세항목 전체를 대체하는 JSON 배열
  - 각 항목은 `name`, `content`, `category` 필드를 포함하며, `id`는 서버가 새로 부여한다
  - REPLACE와 PATCH는 동시에 사용하지 않는다 (AI 프롬프트에서 둘 중 하나만 사용하도록 지시)
- **`chat_stream()` 내부 처리 순서**:
  1. `state.get_original_by_group(req_group)` — 해당 그룹 원본 1건 조회
  2. `state.get_detail_by_group(req_group)` — 해당 그룹 상세항목만 조회
  3. `_build_system_prompt(original_req, filtered_details)` 호출
  4. 스트리밍 중 `<PATCH>` / `<REPLACE>` 태그를 텍스트에서 제거하여 `text` 이벤트 발행
  5. 스트리밍 완료 후 `_process_patches(full_text)` 실행 → `patch` 이벤트들 발행
  6. `_process_replace(full_text, req_group)` 실행 → `replace` 이벤트 발행 (해당 시)
  7. `done` 이벤트
- **에러 처리**: `req_group`에 해당하는 원본 요구사항이 없으면 `error` SSE 이벤트 반환. 그룹 상세항목이 없어도 원본 텍스트만으로 진행 가능 (신규 생성 요청 처리).
- **제약**:
  - `_process_replace` 내부에서 `state.replace_detail_group(req_group, items)` 함수를 호출하여 서버 state를 교체한다.
  - REPLACE 처리 실패 시(JSON 파싱 오류 등) 해당 교체를 건너뛰고 계속 진행한다 — PATCH와 동일한 에러 정책.
  - `chat_service_sdk.py`가 `_build_system_prompt`와 `_process_patches`를 import하므로, `_process_replace`도 동일하게 공개 함수로 유지한다.

#### `backend/app/state.py` 변경 (REQ-004 관련)

- **책임**: 그룹 기준 원본/상세요구사항 조회 및 그룹 단위 상세항목 교체 함수를 추가한다.
- **신규 인터페이스**:
  ```python
  def get_original_by_group(req_group: str) -> OriginalRequirement | None
  def get_detail_by_group(req_group: str) -> list[DetailRequirement]
  def replace_detail_group(req_group: str, items: list[DetailRequirement]) -> None
  ```
- **`get_original_by_group`**: `original_requirements` 목록에서 `id == req_group`인 항목을 반환한다. 없으면 `None`.
- **`get_detail_by_group`**: `detail_requirements` 목록에서 `parent_id == req_group`인 항목을 필터링하여 반환한다.
- **`replace_detail_group`**: `detail_requirements`에서 `parent_id == req_group`인 항목 전체를 `items`로 교체한다. 교체 시 모든 신규 항목의 `is_modified = True`로 설정한다. `_lock`으로 스레드 안전성 보장.
- **결정 근거**: 필터링 로직을 `state.py`에 집중시켜 서비스 계층은 그룹 키만 전달하면 된다. 서비스가 직접 리스트를 순회하면 필터 로직이 분산된다.

#### `backend/app/services/chat_service_sdk.py` 변경

- **책임**: 변경된 `_build_system_prompt` 시그니처와 `_process_replace` 호출에 맞게 조정한다.
- **변경 인터페이스**:
  ```python
  # 기존
  async def chat_stream(session_id, message, history) -> AsyncGenerator[str, None]

  # 변경 후
  async def chat_stream(session_id, message, history, req_group: str) -> AsyncGenerator[str, None]
  ```
- **변경 import**: `_process_replace`를 `chat_service.py`에서 추가로 import한다.
- **변경 범위**: `_build_system_prompt` 호출 시 `original_req`, `filtered_details`를 전달하고, 스트리밍 완료 후 `_process_replace(full_text, req_group)` 호출을 추가한다.
- **제약**: `chat_service.py`에서 `_build_system_prompt`를 import하는 구조가 유지되므로, `chat_service.py` 함수가 변경되면 `chat_service_sdk.py`도 동시에 갱신해야 한다. 두 파일은 항상 동기화 상태여야 한다.

#### SSE 이벤트 추가: `replace` 타입

- **기존 SSE 이벤트**: `text`, `patch`, `done`, `error`
- **신규 추가**: `replace`
  ```json
  {
    "type": "replace",
    "req_group": "REQ-001",
    "items": [
      {"id": "REQ-001-01", "parent_id": "REQ-001", "name": "...", "content": "...", "category": "...", "order_index": 0, "is_modified": true},
      {"id": "REQ-001-02", "parent_id": "REQ-001", "name": "...", "content": "...", "category": "...", "order_index": 1, "is_modified": true}
    ]
  }
  ```
- **`id` 부여 방식**: 서버가 `replace_detail_group()` 내에서 `REQ-{group번호}-{order+1:02d}` 형식으로 새 id를 할당한다. 기존 id 체계와 일치시켜 다운로드·참조 일관성을 유지한다.

#### `frontend/src/store/useAppStore.ts` 변경

- **책임**: 그룹 선택 상태 관리 및 REPLACE 이벤트 처리를 담당한다.
- **신규 상태 필드**:
  ```typescript
  selectedReqGroup: string | null  // 현재 채팅 컨텍스트로 선택된 REQ 그룹 ID
  ```
- **신규 액션**:
  ```typescript
  setSelectedReqGroup: (group: string | null) => void

  replaceDetailReqGroup: (reqGroup: string, items: DetailRequirement[]) => void
  // 동작: detailReqs에서 parent_id === reqGroup인 항목을 items로 전체 교체
  ```
- **`initialState` 변경**: `selectedReqGroup: null` 추가. `reset()` 시 `null`로 초기화됨.
- **제약**: `replaceDetailReqGroup`은 순수 동기 상태 갱신이다. 서버에 별도 API 호출이 없다 — REPLACE는 이미 서버 SSE 이벤트를 통해 서버 state가 갱신된 후 발행된다.

#### `frontend/src/components/ChatPanel.tsx` 변경

- **책임**: 선택된 REQ 그룹을 헤더에 표시하고, 채팅 전송 시 `req_group`을 포함시키며, `replace` SSE 이벤트를 처리한다.
- **변경 props/상태**: `selectedReqGroup`을 `useAppStore`에서 추가로 구독한다.
- **헤더 표시**: `selectedReqGroup`이 있으면 "AI 수정 채팅 — REQ-001 컨텍스트로 대화 중" 형태로 표시한다. `null`이면 기존 "AI 수정 채팅" 텍스트 유지.
- **비활성화 조건 변경**:
  - 기존: `!sessionId || detailReqs.length === 0 || isChatting`
  - 변경: `!sessionId || !selectedReqGroup || detailReqs.length === 0 || isChatting`
  - 이유: REQ 그룹이 선택되지 않은 상태에서 채팅을 허용하면 `req_group` 없이 요청이 전송되어 서버 400 오류가 발생한다.
- **`chatStream` 호출 변경**: 페이로드에 `req_group: selectedReqGroup` 추가.
- **`onReplace` 콜백 추가**:
  - `replaceDetailReqGroup(req_group, items)` 호출
  - `window.dispatchEvent(new CustomEvent('req-group-replace', { detail: req_group }))` 발행 — DetailReqTable이 그룹 전체 행 하이라이트를 위해 구독할 수 있도록 한다
- **변경 색상 구분 표시 (AC-004-06)**:
  - PATCH: 기존 `req-highlight` 이벤트로 개별 행 강조 (변경 없음)
  - REPLACE: `req-group-replace` 이벤트로 해당 그룹 전체 행 강조. DetailReqTable에서 `is_modified === true` 행에 배경색 적용 (이미 `is_modified` 필드가 있으므로 CSS 조건 추가만 필요)

#### `frontend/src/api/index.ts` 변경

- **책임**: `chatStream` 함수에 `onReplace` 콜백과 `req_group` 페이로드를 추가한다.
- **변경 인터페이스**:
  ```typescript
  // 기존 payload
  { session_id: string; message: string; history: {...}[] }

  // 변경 후
  { session_id: string; message: string; history: {...}[]; req_group: string }
  ```
  ```typescript
  // 기존 callbacks
  { onText, onPatch, onDone, onError }

  // 변경 후
  { onText, onPatch, onReplace, onDone, onError }

  // onReplace 시그니처
  onReplace: (reqGroup: string, items: DetailRequirement[]) => void
  ```
- **SSE 파싱 추가**: `json.type === 'replace'` 분기에서 `callbacks.onReplace(json.req_group, json.items)` 호출.
- **제약**: 기존 `onPatch` 콜백과 동일하게 `onReplace`는 선택적으로 제공될 수 있다. 콜백이 없으면 이벤트를 조용히 무시한다.

---

### REQ-009

#### `backend/app/models/session.py` 변경

- **책임**: `sdk_session_id` 단일 필드를 REQ 그룹별 딕셔너리로 교체한다.
- **인터페이스**:
  ```
  SessionState:
    기존 필드 유지 (session_id, status, original_requirements, detail_requirements, chat_messages, created_at)
    - sdk_session_id: str | None = None   ← 제거
    + sdk_sessions: Dict[str, str] = {}   ← 신규 (키: REQ 그룹 ID, 값: SDK session_id)
  ```
- **제약**: `Dict[str, str]` 기본값을 `{}` (빈 딕셔너리)로 설정한다. `reset_session()`이 새 `SessionState()`를 생성할 때 자동으로 초기화된다. Pydantic `Field(default_factory=dict)`를 사용하여 인스턴스 간 딕셔너리 공유를 방지한다.
- **결정 근거**: 기존 `sdk_session_id` 단일 필드는 마지막으로 생성된 REQ 그룹의 세션만 기억할 수 있었다. 여러 REQ 그룹이 각자 세션을 유지하려면 딕셔너리가 필요하다. REQ-009-04(그룹 간 세션 독립성)를 구조적으로 보장한다.

#### `backend/app/state.py` 변경

- **책임**: REQ 그룹 키 기반의 SDK session_id 읽기/쓰기 인터페이스를 제공한다.
- **변경 인터페이스**:
  ```python
  # 기존
  def get_sdk_session_id() -> str | None
  def set_sdk_session_id(session_id: str) -> None

  # 변경 후
  def get_sdk_session_id(req_group: str) -> str | None
  def set_sdk_session_id(req_group: str, session_id: str) -> None
  ```
- **`get_sdk_session_id`**: `sdk_sessions.get(req_group)` — 해당 그룹의 session_id 반환. 없으면 `None`.
- **`set_sdk_session_id`**: `sdk_sessions[req_group] = session_id` — `_lock` 보호 하에 갱신.
- **제약**: 기존 `_lock` 패턴을 동일하게 유지한다. 함수 시그니처 변경이므로 호출 지점(`ai_generate_service_sdk.py`, `chat_service_sdk.py`)도 동시에 갱신해야 한다 (이 설계 문서에서 함께 지정).

#### `backend/app/models/api.py` 변경 (REQ-009 관련)

- **책임**: `GenerateRequest`에 REQ 그룹 정보를 추가한다.
- **인터페이스**:
  ```
  GenerateRequest:
    기존 필드 유지 (session_id)
    + req_group: str  — 생성 대상 REQ 그룹 ID (예: "REQ-001")
  ```
- **제약**: 현재 `generate` API는 전체 원본 요구사항을 일괄 생성한다. REQ-009-01은 "REQ 그룹별 생성을 세션 시작으로 삼는다"고 명시한다. 따라서 `req_group`은 "어느 그룹 생성 완료 후 session_id를 저장할 것인가"를 지정하는 용도이다.
- **가정**: 현재 `generate` API는 단일 호출로 전체 그룹을 생성한다. 그룹별 생성을 개별 API 호출로 분리하지 않는다 — 이는 요구사항 변경이 아닌 구현 상세 결정이다. 단, `req_group`을 받으므로 향후 그룹별 개별 생성 확장이 가능하다.

#### `backend/app/services/ai_generate_service_sdk.py` 변경

- **책임**: 생성 완료 후 session_id를 REQ 그룹 키로 저장한다.
- **변경 인터페이스**:
  ```python
  # 기존
  async def generate_stream(self, session_id: str) -> AsyncGenerator[str, None]

  # 변경 후
  async def generate_stream(self, session_id: str, req_group: str) -> AsyncGenerator[str, None]
  ```
- **변경 범위**: `ResultMessage` 처리 블록에서 `state.set_sdk_session_id(sdk_sid)` → `state.set_sdk_session_id(req_group, sdk_sid)` 로 변경.
- **제약**: `req_group`이 빈 문자열이거나 None이면 session_id 저장을 건너뛴다. 기존의 "session_id 없으면 경고 로그만 남김" 정책과 동일하게 세션 저장 실패가 생성 스트림 전체를 실패시키지 않도록 한다.

#### `backend/app/routers/generate.py` 변경

- **책임**: `generate_stream` 호출 시 `req_group`을 추가로 전달한다.
- **변경 범위**: `service.generate_stream(req.session_id)` → `service.generate_stream(req.session_id, req.req_group)` 로 변경.
- **제약**: `AiGenerateService.generate_stream()`(anthropic_api 경로)은 `req_group` 파라미터가 없다. 라우터는 `AI_BACKEND` 팩토리를 통해 서비스를 주입받으므로, SDK 경로와 API 경로 간 시그니처 불일치가 발생한다. 이를 해결하기 위해 아래 두 방식 중 하나를 선택한다:
  - **방식 A — 조건부 호출**: 라우터에서 서비스 타입을 확인하여 SDK 경로만 `req_group` 전달. 단, 타입 확인은 팩토리 패턴의 추상화를 깨뜨린다.
  - **방식 B — 공통 시그니처**: `AiGenerateService.generate_stream()`에도 `req_group: str = ""` 기본값 파라미터를 추가하여 시그니처를 통일한다. 내부에서는 무시한다.
  - **권장 방식**: 방식 B. 팩토리 패턴을 깨뜨리지 않고 라우터 코드를 단순하게 유지한다. `req_group` 미사용 경로에서 불필요한 필드를 받는 것은 허용 가능한 트레이드오프이다.

---

## API 설계

### 변경된 엔드포인트

| Method | Path | 변경 내용 | 기존 스키마 | 변경 스키마 |
|--------|------|---------|-----------|-----------|
| POST | `/api/v1/chat` | 요청 바디에 `req_group` 추가 | `{session_id, message, history}` | `{session_id, message, history, req_group}` |
| POST | `/api/v1/generate` | 요청 바디에 `req_group` 추가 | `{session_id}` | `{session_id, req_group}` |

### 신규 SSE 이벤트

```
# 기존 (변경 없음)
data: {"type": "text",  "delta": "..."}
data: {"type": "patch", "id": "REQ-001-02", "field": "content", "value": "..."}
data: {"type": "done"}
data: {"type": "error", "message": "..."}

# 신규 추가
data: {"type": "replace", "req_group": "REQ-001", "items": [...]}
```

#### `replace` 이벤트 상세

```json
{
  "type": "replace",
  "req_group": "REQ-001",
  "items": [
    {
      "id": "REQ-001-01",
      "parent_id": "REQ-001",
      "name": "새 상세요구사항 명칭",
      "content": "새 상세 내용",
      "category": "기능 요구사항",
      "order_index": 0,
      "is_modified": true
    }
  ]
}
```

---

## 디렉토리 구조

```
backend/
├── app/
│   ├── models/
│   │   ├── api.py              # [수정] ChatRequest.req_group, GenerateRequest.req_group 추가
│   │   └── session.py          # [수정] sdk_sessions: Dict[str, str] 교체
│   ├── state.py                # [수정] get_original_by_group, get_detail_by_group,
│   │                           #        replace_detail_group, get/set_sdk_session_id(req_group) 추가
│   ├── routers/
│   │   └── generate.py         # [수정] generate_stream(req.session_id, req.req_group) 호출
│   └── services/
│       ├── chat_service.py     # [수정] chat_stream에 req_group 파라미터, _build_system_prompt 시그니처 변경,
│       │                       #        _process_replace() 추가
│       ├── chat_service_sdk.py # [수정] chat_stream에 req_group 전달, _process_replace import/호출
│       ├── ai_generate_service.py  # [수정] generate_stream(session_id, req_group="") 기본값 추가만
│       └── ai_generate_service_sdk.py  # [수정] generate_stream에 req_group, set_sdk_session_id(req_group)

frontend/
└── src/
    ├── api/
    │   └── index.ts            # [수정] chatStream payload에 req_group, onReplace 콜백 추가
    │                           #        generateDetailStream payload에 req_group 추가
    ├── store/
    │   └── useAppStore.ts      # [수정] selectedReqGroup 상태, setSelectedReqGroup,
    │                           #        replaceDetailReqGroup 액션 추가
    └── components/
        └── ChatPanel.tsx       # [수정] selectedReqGroup 구독, 헤더 표시, req_group 전송,
                                #        onReplace 처리, 비활성화 조건 변경
```

---

## 단위 테스트 ID 사전 할당

### REQ-004 (신규 항목)

| UT-ID | 대상 | 설명 | REQ-ID |
|-------|------|------|--------|
| UT-004-06 | `state.get_original_by_group()` | `req_group`에 해당하는 원본 요구사항 1건을 반환함 | REQ-004-05 |
| UT-004-07 | `state.get_detail_by_group()` | `parent_id == req_group`인 상세항목만 반환하고 다른 그룹 항목을 포함하지 않음 | REQ-004-05 |
| UT-004-08 | `state.replace_detail_group()` | 해당 그룹의 기존 상세항목이 전체 교체되고 `is_modified`가 true로 설정됨 | REQ-004-06 |
| UT-004-09 | `state.replace_detail_group()` | 다른 그룹의 상세항목은 변경되지 않음 | REQ-004-06 |
| UT-004-10 | `ChatService.chat_stream()` | `req_group` 전달 시 시스템 프롬프트에 해당 그룹 원본+상세항목만 포함됨 (다른 그룹 상세항목 미포함) | REQ-004-05 |
| UT-004-11 | `ChatService.chat_stream()` | `<REPLACE>[...]</REPLACE>` 태그 감지 시 `replace` SSE 이벤트 발행 및 `state.replace_detail_group()` 호출 | REQ-004-06 |
| UT-004-12 | `ChatService.chat_stream()` | `<REPLACE>` 태그 내부 JSON 파싱 실패 시 replace 이벤트 없이 `done` 이벤트 발행 (스트림 비중단) | REQ-004-06 |
| UT-004-13 | `ChatServiceSDK.chat_stream()` | `req_group` 전달 시 `_build_system_prompt`에 그룹 필터링된 데이터가 전달됨 | REQ-004-05 |
| UT-004-14 | `useAppStore.setSelectedReqGroup` | 호출 후 `selectedReqGroup`이 해당 값으로 갱신됨 | REQ-004-04 |
| UT-004-15 | `useAppStore.replaceDetailReqGroup` | 해당 그룹의 detailReqs가 새 항목으로 교체되고 다른 그룹 항목은 유지됨 | REQ-004-06 |
| UT-004-16 | `chatStream` (api/index.ts) | `replace` SSE 이벤트 수신 시 `onReplace(req_group, items)` 콜백이 호출됨 | REQ-004-06 |
| UT-004-17 | `ChatPanel` | `selectedReqGroup`이 null이면 채팅 입력창이 disabled 상태임 | REQ-004-04 |
| UT-004-18 | `ChatPanel` | `selectedReqGroup`이 설정된 경우 헤더에 해당 그룹 ID가 표시됨 | REQ-004-04 |
| UT-004-19 | `ChatPanel` | `onReplace` 수신 시 `replaceDetailReqGroup` 액션이 호출됨 | REQ-004-06 |

### REQ-009 (신규/수정 항목)

| UT-ID | 대상 | 설명 | REQ-ID |
|-------|------|------|--------|
| UT-009-05 | `SessionState` | `sdk_sessions` 필드의 기본값이 빈 딕셔너리 `{}`임 | REQ-009-03 |
| UT-009-06 | `state.set_sdk_session_id(req_group, session_id)` | 지정한 그룹 키로 저장한 session_id가 `get_sdk_session_id(req_group)`로 조회 시 동일하게 반환됨 | REQ-009-01 |
| UT-009-07 | `state.get_sdk_session_id(req_group)` | 저장되지 않은 그룹 키 조회 시 `None`을 반환함 | REQ-009-01 |
| UT-009-08 | `state.set_sdk_session_id` (그룹 A, B 독립) | REQ-001에 session_id를 저장해도 REQ-002의 session_id에 영향을 주지 않음 | REQ-009-04 |
| UT-009-09 | `state.reset_session()` | 호출 후 `sdk_sessions`이 빈 딕셔너리 `{}`로 초기화됨 | REQ-009-03 |
| UT-009-10 | `AIGenerateServiceSDK.generate_stream()` | 생성 완료 후 `state.get_sdk_session_id(req_group)`에 해당 그룹의 SDK session_id가 저장됨 | REQ-009-01 |
| UT-009-11 | `AIGenerateServiceSDK.generate_stream()` | REQ-001 생성 후 REQ-002 생성 시 각 그룹에 별도 session_id가 저장됨 | REQ-009-04 |
| UT-009-12 | `ChatServiceSDK.chat_stream()` | `req_group` 전달 시 해당 그룹의 session_id만 `ClaudeAgentOptions(resume=...)` 에 사용됨 | REQ-009-02, REQ-009-04 |
| UT-009-13 | `ChatServiceSDK.chat_stream()` | 해당 그룹의 session_id가 없으면 `resume` 없이 새 세션으로 `query()` 호출됨 | REQ-009-02 |

---

## 보안 고려사항

| SEC-ID | 위협 | 대응 방안 | OWASP |
|--------|------|----------|-------|
| SEC-004-03 | `req_group` 파라미터 위변조 — 존재하지 않는 그룹 ID를 전달하여 서버 state 조회 오류 유발 | `state.get_original_by_group()`이 `None`을 반환하면 `error` SSE 이벤트로 응답하고 처리를 중단한다. 빈 문자열은 `min_length=1` Pydantic 제약으로 400 반환. | A03 Injection |
| SEC-004-04 | REPLACE 이벤트의 대량 항목 삽입 — `<REPLACE>` 내부에 수천 개 항목을 포함하여 메모리 과점 | `replace_detail_group()`에서 교체할 최대 항목 수를 제한한다 (예: 기존 그룹 항목 수의 3배 이내). 초과 시 `error` SSE 이벤트 발행. | A05 Security Misconfiguration |
| SEC-004-05 | REPLACE JSON 인젝션 — `<REPLACE>` 내부에 `</REPLACE>` 문자열을 포함하여 태그 파싱 혼란 유발 | REPLACE 태그 파싱은 정규식이 아닌 첫 번째 `<REPLACE>`, 마지막 `</REPLACE>` 경계를 사용하거나, `re.DOTALL`로 처리한다. JSON 파싱 실패 시 조용히 건너뜀. | A03 Injection |
| SEC-009-04 | 그룹 간 세션 크로스오버 — `req_group` 키 오입력으로 다른 그룹 세션에 접근 | `sdk_sessions` 딕셔너리는 서버 state에서만 관리되며 클라이언트에 노출되지 않는다. 그룹 키 충돌은 동일 그룹 재생성 시 덮어쓰기로 처리한다 (신규 세션 시작). | A01 Broken Access Control |
| SEC-009-05 | `sdk_sessions` Dict 무한 증가 — REQ 그룹이 많아질 경우 메모리 점유 | 단일 사용자 로컬 도구이므로 즉각적 위험은 낮다. `reset_session()` 호출 시 전체 초기화된다. 향후 멀티유저 확장 시 그룹 수 상한 검토. | A05 Security Misconfiguration |

---

## 트레이드오프 기록

| 결정 | 선택한 방식 | 대안 | 이유 |
|------|------------|------|------|
| REPLACE 태그 형식 | `<REPLACE>[JSON 배열]</REPLACE>` | REPLACE를 별도 엔드포인트 호출로 처리 | PATCH와 동일한 스트리밍 흐름에서 처리하여 클라이언트 구현 단순화. 별도 엔드포인트는 SSE 완료 후 추가 API 호출이 필요해 타이밍 복잡성이 증가함. |
| PATCH와 REPLACE 동시 사용 금지 | AI 프롬프트에서 둘 중 하나만 사용하도록 지시 | 둘 다 허용하고 처리 순서를 정의 | 동시 사용 시 같은 항목이 PATCH로 수정된 뒤 REPLACE로 덮어쓰이는 순서 의존성이 생긴다. 단순성 우선. |
| `req_group`을 ChatRequest 바디 필드로 포함 | 요청 바디 필드 추가 | URL 경로 파라미터로 분리 (`POST /api/v1/chat/{req_group}`) | 기존 `/api/v1/chat` 경로를 유지하여 프론트엔드 API 호출 URL 변경을 최소화. RESTful 관점에서는 경로 파라미터가 더 명시적이나, 채팅 리소스는 그룹의 하위가 아닌 독립 동작으로 본다. |
| `GenerateRequest.req_group` 추가 | 배치 생성 시 마지막 처리 그룹의 session_id만 저장 | 그룹별 개별 generate 호출로 분리 | 현재 generate는 전체 원본을 일괄 처리한다. 개별 호출로 분리하면 구현 범위가 크게 확장된다. 현 단계에서는 단일 호출로 모든 그룹을 생성하고 `req_group`으로 "기준 그룹"을 지정하는 방식으로 최소 변경한다. |
| `AiGenerateService.generate_stream()`에 `req_group=""` 기본값 추가 | 공통 시그니처 유지 | 라우터에서 서비스 타입을 확인 | 팩토리 추상화를 보존하며 라우터 코드를 단순하게 유지. anthropic_api 경로는 세션 기능이 없으므로 파라미터를 무시해도 기존 동작에 영향 없음. |
| 그룹 전환 시 채팅 히스토리 유지 여부 | 유지 (전환해도 히스토리 보존) | 그룹 전환 시 히스토리 초기화 | AC-004-04는 "채팅창 상단에 컨텍스트 표시"만 명시하고 히스토리 초기화는 언급하지 않는다. 사용자가 이전 대화 맥락을 참조할 수 있도록 유지하는 것이 더 유용하다. 단, 히스토리가 다른 그룹의 맥락을 담고 있어도 서버는 `req_group`으로 컨텍스트를 제한하므로 AI 혼란이 없다. |
