# REQ-008 / REQ-009 설계 문서

> Gate 2 — Architect 작성
> 담당 범위: REQ-008-01 ~ REQ-008-03, REQ-009-01 ~ REQ-009-03

---

## 개요

- **REQ 그룹**: REQ-008 — 인라인 편집 서버 동기화 / REQ-009 — claude_code_sdk 세션 기반 연속 실행
- **설계 방식**: 최소 변경 증분 패치 (Minimal Incremental Change)
- **핵심 결정사항**:
  - REQ-008: `InlineEditRequest` 모델과 `patch_detail()` 함수가 이미 구현되어 있다. 라우터에 `PATCH /api/v1/detail/{id}` 엔드포인트를 추가하고, 프론트엔드 `api/index.ts`에 `patchDetailReq` 호출을 추가하는 것만으로 완결된다.
  - REQ-009: `SessionState`에 `sdk_session_id` 필드를 추가하고, `AIGenerateServiceSDK`가 `ResultMessage`에서 session_id를 추출하여 저장하며, `ChatServiceSDK`가 저장된 session_id를 `ClaudeAgentOptions(resume=...)` 에 전달한다. 새 HWP 업로드 시 `reset_session()`이 자동으로 초기화하므로 별도 초기화 로직은 불필요하다.

---

## 변경 대상 파일 목록

### REQ-008

| 파일 경로 | 변경 유형 | 변경 내용 요약 |
|----------|----------|--------------|
| `backend/app/routers/detail.py` | 신규 | `PATCH /api/v1/detail/{id}` 엔드포인트 |
| `backend/app/main.py` | 수정 | `detail` 라우터 등록 |
| `frontend/src/api/index.ts` | 수정 | `patchDetailReq()` 함수 추가 |
| `frontend/src/store/useAppStore.ts` | 수정 | `patchDetailReq` 액션에서 API 호출 추가 (또는 별도 thunk 방식으로 호출) |

### 불변 파일 (REQ-008)

| 파일 경로 | 이유 |
|----------|------|
| `backend/app/models/api.py` | `InlineEditRequest` 모델 이미 구현 완료 |
| `backend/app/state.py` | `patch_detail()` 함수 이미 구현 완료 |

### REQ-009

| 파일 경로 | 변경 유형 | 변경 내용 요약 |
|----------|----------|--------------|
| `backend/app/models/session.py` | 수정 | `SessionState`에 `sdk_session_id: str | None` 필드 추가 |
| `backend/app/state.py` | 수정 | `get_sdk_session_id()`, `set_sdk_session_id()` 함수 추가 |
| `backend/app/services/ai_generate_service_sdk.py` | 수정 | 생성 완료 후 `ResultMessage`에서 `session_id` 추출·저장 |
| `backend/app/services/chat_service_sdk.py` | 수정 | `query()` 호출 시 `ClaudeAgentOptions(resume=sdk_session_id)` 적용 |

### 불변 파일 (REQ-009)

| 파일 경로 | 이유 |
|----------|------|
| `backend/app/routers/generate.py` | 라우터 인터페이스 변경 없음 |
| `backend/app/routers/chat.py` | 라우터 인터페이스 변경 없음 |
| `backend/app/services/ai_generate_service.py` | Anthropic API 경로 — 세션 기능 해당 없음 |
| `backend/app/services/chat_service.py` | 동일 이유 |
| 프론트엔드 전체 | 서버 내부 세션 관리이므로 클라이언트 변경 없음 |

---

## 시스템 구조

### REQ-008 데이터 흐름

```
[프론트엔드]
  DetailTable 셀 blur 이벤트
    → patchDetailReq(id, field, value) 호출 (useAppStore)
        → patchDetailReq API 함수 호출 (api/index.ts)
            → PATCH /api/v1/detail/{id}  { field, value }
                → detail 라우터
                    → state.patch_detail(id, field, value)
                        → 성공: 수정된 DetailRequirement 반환
                        → 실패(id 없음): 404 응답
        → 응답 성공 시 Zustand 스토어 갱신
        → 응답 실패 시 에러 상태 설정 (롤백 또는 에러 표시)
```

### REQ-009 데이터 흐름

```
[최초 생성 — sdk_session_id 없음]
  POST /api/generate
    → AIGenerateServiceSDK.generate_stream()
        → query(full_prompt, ClaudeAgentOptions(allowed_tools=[]))
            → AssistantMessage 스트리밍 처리 (기존 로직)
            → ResultMessage 수신
                → ResultMessage.session_id 추출
                → state.set_sdk_session_id(session_id) 저장
        → SSE done 이벤트 발행

[이후 채팅 — sdk_session_id 존재]
  POST /api/chat
    → ChatServiceSDK.chat_stream()
        → state.get_sdk_session_id() 조회
        → sdk_session_id가 None이면 → 새 세션으로 query() 호출
        → sdk_session_id가 있으면 → ClaudeAgentOptions(resume=sdk_session_id)로 query() 호출
            → AI가 이전 생성 컨텍스트를 이어받아 수정 결과 반환

[새 HWP 업로드 또는 재생성]
  POST /api/upload 또는 "새로 생성" 트리거
    → state.reset_session()
        → SessionState 전체 초기화 (sdk_session_id 포함 → None)
    → 다음 생성 요청은 새 세션으로 시작
```

---

## 모듈/컴포넌트 설계

### REQ-008

#### `backend/app/routers/detail.py` (신규)

- **책임**: `PATCH /api/v1/detail/{id}` 요청을 수신하여 `state.patch_detail()`을 호출하고, 결과를 JSON으로 반환한다.
- **인터페이스**:
  ```
  PATCH /api/v1/detail/{id}
    요청 바디: InlineEditRequest { detail_id: str, field: Literal["name","content","category"], value: str }
    성공 응답 (200): DetailRequirement (수정된 항목 전체)
    실패 응답 (404): ErrorResponse { code: "NOT_FOUND", message: "..." }
  ```
- **제약**:
  - `field` 값은 `InlineEditRequest` 모델의 `Literal` 타입으로 이미 "name", "content", "category" 세 값만 허용된다. 임의 필드 덮어쓰기를 방지한다 (SEC-008-01).
  - `patch_detail()`이 `False`를 반환하면 404로 응답한다. 상세요구사항이 생성되기 전 호출을 방어한다.
  - 경로 파라미터 `{id}`와 바디의 `detail_id`가 모두 존재한다. 라우터는 경로 파라미터만 사용하며 바디의 `detail_id`와 일치 여부를 검증하거나, 바디의 `detail_id`만 사용하는 두 방식 중 하나를 선택한다. 단순성을 위해 경로 파라미터 `id`를 `patch_detail()` 의 `req_id` 인자로 전달하고, 바디는 `field`와 `value`만 사용하도록 한다.
  - 결정 근거: `InlineEditRequest`에 `detail_id` 필드가 있지만, RESTful 관례상 리소스 식별자는 경로에 두는 것이 명확하다. 경로 파라미터를 권위 있는 식별자로 사용한다.

#### `backend/app/main.py` 변경

- **변경 내용**: `detail` 라우터를 `include_router()`로 등록한다.
- **제약**: 기존 라우터(upload, generate, chat, download) 등록 구조와 동일한 패턴을 따른다.

#### `frontend/src/api/index.ts` 변경

- **책임**: `PATCH /api/v1/detail/{id}` 를 호출하는 `patchDetailReq()` 함수를 추가한다.
- **인터페이스**:
  ```typescript
  async function patchDetailReq(
    id: string,
    field: 'name' | 'content' | 'category',
    value: string
  ): Promise<DetailRequirement>
  ```
- **에러 처리**: axios가 `404` 또는 네트워크 오류 발생 시 예외를 throw한다. 호출자(스토어 또는 컴포넌트)가 `catch`하여 에러 상태를 설정한다.
- **결정 근거**: 기존 `uploadHwp()`와 동일하게 axios를 사용한다. SSE 스트림이 아니므로 `fetch + ReadableStream` 패턴을 사용할 필요가 없다.

#### `frontend/src/store/useAppStore.ts` 변경

- **책임**: 인라인 편집 완료 시 서버 동기화를 수행한다.
- **변경 범위**: `patchDetailReq` 액션은 현재 Zustand 스토어 내에서만 상태를 갱신한다. REQ-008-02에 따라 서버 API 호출이 필요하므로, 아래 두 방식 중 하나를 선택한다.
  - **방식 A — 액션 분리**: 기존 `patchDetailReq` (스토어 내 동기 갱신) 는 유지하고, 별도의 비동기 헬퍼 함수 `syncPatchDetailReq(id, field, value)`를 `api/index.ts` 또는 커스텀 훅에 추가한다. 컴포넌트에서 blur 이벤트 시 `syncPatchDetailReq`를 호출하고, 성공 응답을 받은 뒤 `patchDetailReq`를 호출하여 스토어를 갱신한다.
  - **방식 B — 액션 내 비동기**: `patchDetailReq` 액션을 비동기 함수로 변경하여 API 호출 후 스토어를 갱신한다. Zustand는 비동기 액션을 기본 지원한다.
  - **권장 방식**: 방식 A. `patchDetailReq`가 순수 동기 상태 갱신으로 유지되어 기존 채팅 패치 경로(SSE `patch` 이벤트)와 인터페이스가 동일하게 유지된다. 비동기 로직은 컴포넌트 또는 별도 훅이 담당한다.
- **에러 처리**: API 호출 실패 시 스토어를 갱신하지 않고 `setError()`를 호출하여 에러 메시지를 표시한다. 낙관적 업데이트(Optimistic Update)는 사용하지 않는다 — 서버 응답 확인 후 갱신하여 데이터 일관성을 우선한다 (AC-008-03).

---

### REQ-009

#### `backend/app/models/session.py` 변경

- **책임**: `SessionState`에 SDK 세션 연속성을 위한 `sdk_session_id` 필드를 추가한다.
- **인터페이스**:
  ```
  SessionState:
    기존 필드 유지
    + sdk_session_id: str | None = None  (claude-agent-sdk가 반환한 session_id)
  ```
- **제약**: 필드 기본값이 `None`이므로 `reset_session()`이 새 `SessionState()`를 생성할 때 자동으로 `None`으로 초기화된다. 별도 초기화 코드가 불필요하다 (AC-009-03).

#### `backend/app/state.py` 변경

- **책임**: `sdk_session_id`에 대한 읽기/쓰기 함수를 추가한다.
- **인터페이스**:
  ```python
  def get_sdk_session_id() -> str | None
  def set_sdk_session_id(session_id: str) -> None
  ```
- **제약**: 기존 `set_original()`, `set_detail()` 패턴과 동일하게 `_lock`을 사용하여 스레드 안전성을 보장한다.

#### `backend/app/services/ai_generate_service_sdk.py` 변경

- **책임**: 생성 완료 후 `ResultMessage`에서 `session_id`를 추출하여 `state.set_sdk_session_id()`에 저장한다.
- **변경 범위**: `ResultMessage` 처리 블록에 session_id 추출 및 저장 로직을 추가한다.
- **session_id 추출 방법**:
  - `claude-agent-sdk`의 `ResultMessage`는 `session_id` 속성을 가진다.
  - 현재 `generate_stream()`에서 `ResultMessage` 인스턴스는 이미 수신되고 있다. `isinstance(message, ResultMessage)` 분기에서 `message.session_id`를 읽어 저장한다.
  - `session_id`가 `None`이거나 빈 문자열인 경우(SDK가 session_id를 미반환하는 환경)에는 저장하지 않고 경고 로그만 남긴다. 이 경우 이후 채팅은 session_id 없이 동작한다 (기존 동작 유지).
  - `ResultMessage` 스펙 참조:

    ```
    ResultMessage 속성:
      .session_id: str | None   ← SDK 실행 세션 식별자
      .result: str | None       ← 최종 응답 텍스트 (기존 코드에서 이미 사용 중)
      .total_cost_usd: float | None
    ```

- **제약**: session_id 저장 실패가 생성 스트림 전체를 실패시켜서는 안 된다. try/except로 격리하거나 `if session_id:` 가드로 처리한다.
- **결정 근거**: `ResultMessage`는 SDK 실행이 완전히 종료된 시점에 한 번만 발행된다. 스트리밍 도중 session_id를 저장하려 하면 부분 완료 상태에서 채팅이 잘못된 세션을 이어받을 수 있다. 따라서 `ResultMessage` 수신 시점에 저장한다.

#### `backend/app/services/chat_service_sdk.py` 변경

- **책임**: `query()` 호출 시 저장된 `sdk_session_id`를 `ClaudeAgentOptions`의 `resume` 파라미터에 전달하여 이전 생성 세션을 이어받는다.
- **변경 범위**: `ClaudeAgentOptions` 생성 시 `resume` 파라미터 조건부 추가.
- **세션 이어받기 로직**:
  - `state.get_sdk_session_id()`를 호출하여 저장된 session_id를 확인한다.
  - session_id가 `None`이면 `ClaudeAgentOptions(allowed_tools=[], ...)` — 기존과 동일 (새 세션 시작).
  - session_id가 있으면 `ClaudeAgentOptions(allowed_tools=[], resume=sdk_session_id, ...)` — 이전 세션 이어받기.
  - `resume` 파라미터를 사용하면 SDK가 이전 실행의 컨텍스트(생성한 상세요구사항 포함)를 유지한다.
- **제약**:
  - `resume` 파라미터에 유효하지 않은 session_id가 전달되면 SDK가 예외를 발생시킬 수 있다. 기존 `except Exception` 블록이 이를 포착하여 `error` SSE 이벤트로 변환하므로 별도 예외 처리는 불필요하다.
  - `claude_code_sdk` 백엔드에서만 `sdk_session_id`를 사용한다. `anthropic_api` 경로의 `ChatService`는 이 필드를 참조하지 않는다.

---

## API 설계

### REQ-008: PATCH 엔드포인트

| Method | Path | 설명 | 인증 | 요청 바디 | 성공 응답 | 실패 응답 |
|--------|------|------|------|---------|---------|---------|
| PATCH | `/api/v1/detail/{id}` | 특정 상세요구사항의 단일 필드 수정 | 없음 | `InlineEditRequest` | `DetailRequirement` (200) | `ErrorResponse` (404) |

#### 요청 스키마

```
PATCH /api/v1/detail/{id}
Content-Type: application/json

{
  "detail_id": "REQ-001-02",        // 경로 파라미터 id와 동일한 값 권장
  "field": "content",               // "name" | "content" | "category" 중 하나
  "value": "수정된 내용 텍스트"
}
```

참고: `InlineEditRequest` 모델은 `backend/app/models/api.py`에 이미 정의되어 있다.

```python
class InlineEditRequest(BaseModel):
    detail_id: str
    field: Literal["name", "content", "category"]
    value: str
```

#### 성공 응답 스키마 (200)

```json
{
  "id": "REQ-001-02",
  "parent_id": "REQ-001",
  "category": "기능 요구사항",
  "name": "로그인 기능",
  "content": "수정된 내용 텍스트",
  "order_index": 1,
  "is_modified": true
}
```

#### 실패 응답 스키마 (404)

```json
{
  "code": "NOT_FOUND",
  "message": "해당 ID의 상세요구사항을 찾을 수 없습니다: REQ-001-02"
}
```

#### 응답 상태 코드 정의

| 상태 코드 | 발생 조건 |
|---------|---------|
| 200 | `patch_detail()` 성공 — 수정된 `DetailRequirement` 반환 |
| 404 | 해당 `id`가 `detail_requirements` 목록에 없음 (`patch_detail()` → `False` 반환) |
| 422 | Pydantic 유효성 검증 실패 — `field` 값이 허용 범위 외이거나 필드 누락 |

---

## 디렉토리 구조

```
backend/
├── app/
│   ├── main.py                           # [수정] detail 라우터 등록
│   ├── state.py                          # [수정] get_sdk_session_id(), set_sdk_session_id() 추가
│   ├── models/
│   │   ├── api.py                        # [불변] InlineEditRequest 이미 정의
│   │   └── session.py                    # [수정] sdk_session_id 필드 추가
│   ├── routers/
│   │   ├── detail.py                     # [신규] PATCH /api/v1/detail/{id}
│   │   ├── generate.py                   # [불변]
│   │   └── chat.py                       # [불변]
│   └── services/
│       ├── ai_generate_service_sdk.py    # [수정] ResultMessage에서 session_id 추출·저장
│       └── chat_service_sdk.py           # [수정] ClaudeAgentOptions(resume=...) 적용

frontend/
└── src/
    ├── api/
    │   └── index.ts                      # [수정] patchDetailReq() 함수 추가
    └── store/
        └── useAppStore.ts                # [수정] 인라인 편집 시 API 호출 연결
```

---

## 단위 테스트 ID 사전 할당

### REQ-008

| UT-ID | 대상 | 설명 | REQ-ID |
|-------|------|------|--------|
| UT-008-01 | `PATCH /api/v1/detail/{id}` | 유효한 id와 field로 요청 시 수정된 `DetailRequirement` 반환 (200) | REQ-008-01 |
| UT-008-02 | `PATCH /api/v1/detail/{id}` | 존재하지 않는 id로 요청 시 404 반환 | REQ-008-01 |
| UT-008-03 | `PATCH /api/v1/detail/{id}` | `field` 값이 "name", "content", "category" 외의 값이면 422 반환 | REQ-008-01 |
| UT-008-04 | `PATCH /api/v1/detail/{id}` | 수정 후 `state.get_detail()` 목록에서 해당 항목의 값이 변경되어 있음 | REQ-008-03 |
| UT-008-05 | `PATCH /api/v1/detail/{id}` | 수정 후 해당 항목의 `is_modified`가 `true`로 설정됨 | REQ-008-01 |
| UT-008-06 | `patchDetailReq()` (프론트엔드 api) | 정상 응답 시 `DetailRequirement` 객체를 반환함 | REQ-008-02 |
| UT-008-07 | `patchDetailReq()` (프론트엔드 api) | 서버 404 응답 시 예외를 throw함 | REQ-008-02 |
| UT-008-08 | `useAppStore.patchDetailReq` (또는 sync 헬퍼) | API 성공 후 Zustand 스토어의 해당 항목 field 값이 갱신됨 | REQ-008-02, REQ-008-03 |
| UT-008-09 | `useAppStore.patchDetailReq` (또는 sync 헬퍼) | API 실패 시 스토어 값은 변경되지 않고 에러 상태가 설정됨 | REQ-008-02 |

### REQ-009

| UT-ID | 대상 | 설명 | REQ-ID |
|-------|------|------|--------|
| UT-009-01 | `AIGenerateServiceSDK.generate_stream()` | 생성 완료 후 `state.get_sdk_session_id()`에 SDK session_id가 저장됨 | REQ-009-01 |
| UT-009-02 | `AIGenerateServiceSDK.generate_stream()` | `ResultMessage.session_id`가 None인 경우 state 저장 없이 스트림이 정상 완료됨 | REQ-009-01 |
| UT-009-03 | `ChatServiceSDK.chat_stream()` | `state.get_sdk_session_id()`가 None이면 `resume` 없이 `query()` 호출됨 | REQ-009-02 |
| UT-009-04 | `ChatServiceSDK.chat_stream()` | `state.get_sdk_session_id()`가 유효한 값이면 `ClaudeAgentOptions(resume=session_id)`로 `query()` 호출됨 | REQ-009-02 |
| UT-009-05 | `state.reset_session()` | 호출 후 `state.get_sdk_session_id()`가 `None`을 반환함 | REQ-009-03 |
| UT-009-06 | `state.set_sdk_session_id()` / `get_sdk_session_id()` | 저장한 값이 조회 시 동일하게 반환됨 | REQ-009-01 |
| UT-009-07 | `SessionState` | `sdk_session_id` 필드의 기본값이 `None`임 | REQ-009-03 |

---

## 보안 고려사항

| SEC-ID | 위협 | 대응 방안 | OWASP |
|--------|------|----------|-------|
| SEC-008-01 | 임의 필드 덮어쓰기 — `field` 파라미터로 `id`, `parent_id`, `is_modified` 등 내부 필드를 변조 | `InlineEditRequest.field`를 `Literal["name", "content", "category"]`로 제한 (이미 구현됨). Pydantic이 자동 422 반환. | A03 Injection |
| SEC-008-02 | 대량 편집 공격 — 다수의 PATCH 요청으로 전체 상세요구사항 데이터 변조 | 단일 사용자 로컬 도구이므로 즉각적 위험은 낮음. 향후 멀티유저 확장 시 요청 속도 제한(Rate Limiting) 검토. | A05 Security Misconfiguration |
| SEC-008-03 | `value` 필드의 초대형 문자열 입력 — 메모리 과점 또는 다운스트림 AI 호출 시 과금 폭증 | `InlineEditRequest.value`에 최대 길이 제한 추가를 권장한다. `chat_service.py`의 `MAX_MESSAGE_LENGTH`(2000자)와 동일한 기준을 적용하거나, 상세요구사항 내용 특성상 더 긴 값(예: 5000자)이 필요하면 별도 상수로 정의한다. | A03 Injection |
| SEC-009-01 | SDK session_id 위변조 — 클라이언트가 session_id를 직접 전달하거나 조작 | `sdk_session_id`는 서버 state에서만 관리되며 클라이언트에 노출되지 않는다. 클라이언트는 session_id를 알지 못하며 전달할 경로가 없다. | A01 Broken Access Control |
| SEC-009-02 | 만료된 session_id로 resume 시도 — SDK가 유효하지 않은 session_id를 거부하고 예외 발생 | `ChatServiceSDK`의 기존 `except Exception` 블록이 SDK 예외를 `error` SSE 이벤트로 변환한다. 단, 에러 메시지에 session_id 값이 포함되지 않도록 주의한다 (내부 값 노출 방지). | A02 Cryptographic Failures |
| SEC-009-03 | state 경쟁 조건 — 동시 요청에서 `sdk_session_id` 읽기/쓰기 충돌 | `state.py`의 기존 `_lock` 패턴을 `set_sdk_session_id()` / `get_sdk_session_id()`에도 동일하게 적용한다. | A05 Security Misconfiguration |

---

## 트레이드오프 기록

| 결정 | 선택한 방식 | 대안 | 이유 |
|------|------------|------|------|
| PATCH 엔드포인트 경로 파라미터 | 경로 `{id}` 를 권위 있는 식별자로 사용 | 바디의 `detail_id`만 사용 | RESTful 관례 준수. 경로에 리소스 식별자를 두면 라우팅 로그에서 어떤 리소스가 수정됐는지 즉시 확인 가능. |
| 인라인 편집 스토어 동기화 방식 | 방식 A — API 호출 성공 후 스토어 갱신 (비낙관적) | 방식 B — 즉시 스토어 갱신 후 백그라운드 API 호출 (낙관적) | AC-008-03에서 서버-클라이언트 일관성 보장이 명시적 요구사항. 낙관적 업데이트는 롤백 로직이 복잡해지고 채팅 AI가 stale 데이터를 보게 될 위험이 있음. |
| session_id 저장 시점 | `ResultMessage` 수신 완료 시점 | 첫 번째 `AssistantMessage` 수신 시점 | `ResultMessage`는 SDK 실행 완전 종료를 보장하는 신호. 중간에 저장하면 스트리밍 오류로 인한 불완전 세션이 저장될 수 있음. |
| sdk_session_id None 처리 | 저장 건너뜀, 이후 채팅은 새 세션으로 동작 | 에러로 처리하여 생성 스트림 실패 | session_id 미취득은 세션 연속성 기능 미작동이지, 생성 자체의 실패가 아님. 기능 저하(degradation)로 처리하는 것이 더 견고함. |
| REQ-009 프론트엔드 영향 | 변경 없음 | 프론트엔드에 세션 상태 표시 추가 | sdk_session_id는 서버 내부 구현 세부사항. 프론트엔드가 이를 알 필요가 없고, 숨겨진 상태 노출은 불필요한 복잡성을 추가함. |
