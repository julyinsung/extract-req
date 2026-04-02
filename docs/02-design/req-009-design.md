# REQ-009 설계 문서 — claude_code_sdk 세션 기반 연속 실행

> Gate 2 — Architect 작성

---

## 개요

`claude_code_sdk` 백엔드에서 생성(`/api/generate`)과 채팅(`/api/chat`)을 하나의 연속 세션으로 이어받는다.
AI가 자신이 생성한 내용을 기억한 채로 수정 요청을 처리할 수 있게 된다.

**프론트엔드 변경 없음** — 서버 내부 세션 관리이므로 클라이언트에 영향 없다.
`anthropic_api` 백엔드는 현행 방식(전체 JSON 직렬화) 그대로 유지한다.

---

## 변경 파일 요약

| 담당 | 파일 | 변경 유형 |
|------|------|----------|
| **백엔드** | `backend/app/models/session.py` | 수정 — `sdk_session_id` 필드 추가 |
| **백엔드** | `backend/app/state.py` | 수정 — `get/set_sdk_session_id()` 추가 |
| **백엔드** | `backend/app/services/ai_generate_service_sdk.py` | 수정 — session_id 추출·저장 |
| **백엔드** | `backend/app/services/chat_service_sdk.py` | 수정 — `resume=session_id` 적용 |
| 불변 | `backend/app/routers/generate.py` | 라우터 인터페이스 변경 없음 |
| 불변 | `backend/app/routers/chat.py` | 라우터 인터페이스 변경 없음 |
| 불변 | `backend/app/services/ai_generate_service.py` | anthropic_api 경로 — 해당 없음 |
| 불변 | `backend/app/services/chat_service.py` | 동일 이유 |
| 불변 | 프론트엔드 전체 | 변경 없음 |

---

## 백엔드 설계

### 데이터 흐름

```
[최초 생성]
  POST /api/generate
    → AIGenerateServiceSDK.generate_stream()
        → query(full_prompt, ClaudeAgentOptions(allowed_tools=[]))
            → ResultMessage 수신
                → message.session_id 추출
                → state.set_sdk_session_id(session_id) 저장
        → SSE done 이벤트 발행

[이후 채팅]
  POST /api/chat
    → ChatServiceSDK.chat_stream()
        → sdk_session_id = state.get_sdk_session_id()
        → None이면  → ClaudeAgentOptions()            (새 세션 — 기존 동작)
        → 있으면    → ClaudeAgentOptions(resume=...)  (이전 세션 이어받기)

[세션 초기화 — AC-009-03]
  POST /api/upload (새 HWP 업로드) 또는 재생성 트리거
    → state.reset_session()
        → SessionState() 새 인스턴스 생성
        → sdk_session_id = None  (기본값으로 자동 초기화)
```

---

### 수정 파일 1: `backend/app/models/session.py`

`SessionState`에 필드 1개 추가:

```python
sdk_session_id: str | None = None
```

`reset_session()`이 `SessionState()` 새 인스턴스를 생성하므로 자동으로 `None` 초기화됨 — 별도 초기화 코드 불필요 (AC-009-03).

---

### 수정 파일 2: `backend/app/state.py`

기존 `_lock` 패턴과 동일하게 읽기/쓰기 함수 2개 추가:

```python
def get_sdk_session_id() -> str | None:
    with _lock:
        return _session.sdk_session_id

def set_sdk_session_id(session_id: str) -> None:
    with _lock:
        _session.sdk_session_id = session_id
```

---

### 수정 파일 3: `backend/app/services/ai_generate_service_sdk.py`

`ResultMessage` 처리 블록에 session_id 저장 로직 추가:

```python
elif isinstance(message, ResultMessage):
    # 기존 buf 처리 로직 유지
    ...
    # session_id 저장 (REQ-009-01)
    if message.session_id:
        state.set_sdk_session_id(message.session_id)
    else:
        logger.warning("ResultMessage.session_id가 None — 세션 연속성 비활성화")
```

- **저장 시점**: `ResultMessage` 수신 완료 후 — SDK 실행 완전 종료를 보장하는 신호
- `session_id`가 None이면 경고 로그만 남기고 스트림은 정상 완료 (기능 저하로 처리)

#### `ResultMessage` 속성 참조

| 속성 | 타입 | 설명 |
|------|------|------|
| `session_id` | `str \| None` | SDK 실행 세션 식별자 |
| `result` | `str \| None` | 최종 응답 텍스트 (기존 코드에서 이미 사용) |
| `total_cost_usd` | `float \| None` | 비용 정보 |

---

### 수정 파일 4: `backend/app/services/chat_service_sdk.py`

`ClaudeAgentOptions` 생성 시 `resume` 조건부 적용:

```python
sdk_session_id = state.get_sdk_session_id()
options = ClaudeAgentOptions(
    allowed_tools=[],
    permission_mode="default",
    cli_path=cli_path,
    **({"resume": sdk_session_id} if sdk_session_id else {}),
)
```

- 기존 `except Exception` 블록이 유효하지 않은 session_id로 인한 SDK 예외를 `error` SSE 이벤트로 변환하므로 별도 예외 처리 불필요
- 에러 메시지에 `session_id` 값이 노출되지 않도록 주의 (SEC-009-02)

---

### 보안 고려사항

| SEC-ID | 위협 | 대응 |
|--------|------|------|
| SEC-009-01 | session_id 클라이언트 노출 | 서버 state에서만 관리, 응답 바디에 포함 안 됨 |
| SEC-009-02 | 만료 session_id로 resume | 기존 `except Exception` → `error` SSE. 에러 메시지에 session_id 값 미포함 |
| SEC-009-03 | state 경쟁 조건 | 기존 `_lock` 패턴 동일 적용 |

---

### 단위 테스트 (백엔드)

| UT-ID | 대상 | 설명 |
|-------|------|------|
| UT-009-01 | `AIGenerateServiceSDK` | 생성 완료 후 `state.get_sdk_session_id()`에 값 저장 확인 |
| UT-009-02 | `AIGenerateServiceSDK` | `ResultMessage.session_id` None → 저장 없이 정상 완료 |
| UT-009-03 | `ChatServiceSDK` | `sdk_session_id` None → `resume` 없이 `query()` 호출 확인 |
| UT-009-04 | `ChatServiceSDK` | `sdk_session_id` 있음 → `ClaudeAgentOptions(resume=...)` 적용 확인 |
| UT-009-05 | `state.reset_session()` | 호출 후 `get_sdk_session_id()` → `None` |
| UT-009-06 | `state` 읽기/쓰기 | 저장한 session_id가 조회 시 동일하게 반환 |
| UT-009-07 | `SessionState` | `sdk_session_id` 기본값 `None` 확인 |

---

## 프론트엔드 설계

**변경 없음.** `sdk_session_id`는 서버 내부 구현 세부사항으로 클라이언트에 노출하지 않는다.
