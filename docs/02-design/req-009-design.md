# REQ-009 설계 문서 — claude_code_sdk 세션 기반 연속 실행

> Gate 2 — Architect 작성
> 전체 설계: `req-008-009-design.md` 참조

---

## 개요

현재 `claude_code_sdk` 백엔드는 생성과 채팅을 독립된 `query()` 호출로 처리한다.
`resume=session_id`를 활용하여 최초 생성 세션을 채팅까지 이어받으면 AI가 자신이 생성한 내용을 기억한 채로 수정 요청을 처리할 수 있다.

`anthropic_api` 백엔드는 현행 방식(전체 JSON 직렬화) 그대로 유지한다.

---

## 변경 대상 파일

| 파일 경로 | 변경 유형 | 내용 |
|----------|----------|------|
| `backend/app/models/session.py` | 수정 | `SessionState`에 `sdk_session_id: str \| None = None` 추가 |
| `backend/app/state.py` | 수정 | `get_sdk_session_id()`, `set_sdk_session_id()` 추가 |
| `backend/app/services/ai_generate_service_sdk.py` | 수정 | `ResultMessage`에서 `session_id` 추출·저장 |
| `backend/app/services/chat_service_sdk.py` | 수정 | `ClaudeAgentOptions(resume=sdk_session_id)` 적용 |

### 불변 파일

| 파일 경로 | 이유 |
|----------|------|
| `backend/app/routers/generate.py` | 라우터 인터페이스 변경 없음 |
| `backend/app/routers/chat.py` | 라우터 인터페이스 변경 없음 |
| `backend/app/services/ai_generate_service.py` | anthropic_api 경로 — 해당 없음 |
| `backend/app/services/chat_service.py` | 동일 이유 |
| 프론트엔드 전체 | 서버 내부 세션 관리 — 클라이언트 변경 없음 |

---

## 데이터 흐름

```
[최초 생성]
  POST /api/generate
    → AIGenerateServiceSDK.generate_stream()
        → query(full_prompt, ClaudeAgentOptions(allowed_tools=[]))
            → ResultMessage 수신
                → message.session_id 추출
                → state.set_sdk_session_id(session_id)

[이후 채팅]
  POST /api/chat
    → ChatServiceSDK.chat_stream()
        → sdk_session_id = state.get_sdk_session_id()
        → sdk_session_id가 None  → ClaudeAgentOptions() 기존 방식
        → sdk_session_id가 있음  → ClaudeAgentOptions(resume=sdk_session_id)
            → AI가 생성 컨텍스트를 이어받아 수정

[세션 초기화 — AC-009-03]
  POST /api/upload (새 HWP) 또는 재생성 트리거
    → state.reset_session()
        → SessionState() 새 인스턴스 생성
        → sdk_session_id = None (기본값으로 자동 초기화)
```

---

## 모듈 변경 상세

### `backend/app/models/session.py`

```python
class SessionState(BaseModel):
    # 기존 필드 유지
    ...
    sdk_session_id: str | None = None  # 추가
```

`reset_session()`이 `SessionState()`를 새로 생성하므로 자동으로 `None` 초기화됨 (AC-009-03 무료 달성).

---

### `backend/app/state.py`

기존 `_lock` 패턴 그대로 적용:

```python
def get_sdk_session_id() -> str | None:
    with _lock:
        return _session.sdk_session_id

def set_sdk_session_id(session_id: str) -> None:
    with _lock:
        _session.sdk_session_id = session_id
```

---

### `backend/app/services/ai_generate_service_sdk.py`

`ResultMessage` 분기에 session_id 저장 추가:

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

`session_id` 저장 실패가 생성 스트림을 실패시켜선 안 되므로 `if` 가드로 처리한다.

---

### `backend/app/services/chat_service_sdk.py`

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

기존 `except Exception` 블록이 유효하지 않은 session_id로 인한 SDK 예외를 `error` SSE 이벤트로 변환하므로 별도 예외 처리 불필요.

---

## 단위 테스트 ID

| UT-ID | 대상 | 설명 |
|-------|------|------|
| UT-009-01 | `AIGenerateServiceSDK` | 생성 완료 후 `state.get_sdk_session_id()`에 값 저장 확인 |
| UT-009-02 | `AIGenerateServiceSDK` | `ResultMessage.session_id`가 None이면 저장 없이 정상 완료 |
| UT-009-03 | `ChatServiceSDK` | `sdk_session_id` None이면 `resume` 없이 `query()` 호출 |
| UT-009-04 | `ChatServiceSDK` | `sdk_session_id` 있으면 `ClaudeAgentOptions(resume=...)` 적용 |
| UT-009-05 | `state.reset_session()` | 호출 후 `get_sdk_session_id()` → `None` |
| UT-009-06 | `state` 읽기/쓰기 | 저장한 session_id가 조회 시 동일하게 반환 |
| UT-009-07 | `SessionState` | `sdk_session_id` 기본값이 `None` |

---

## 보안 고려사항

| SEC-ID | 위협 | 대응 |
|--------|------|------|
| SEC-009-01 | session_id 클라이언트 노출 | `sdk_session_id`는 서버 state에서만 관리, 응답 바디에 포함 안 됨 |
| SEC-009-02 | 만료된 session_id로 resume | 기존 `except Exception` → `error` SSE 변환. 에러 메시지에 session_id 값 미포함 |
| SEC-009-03 | state 경쟁 조건 | 기존 `_lock` 패턴을 새 함수에도 동일 적용 |

---

## 트레이드오프

| 결정 | 선택 | 대안 | 이유 |
|------|------|------|------|
| session_id 저장 시점 | `ResultMessage` 수신 완료 후 | 첫 `AssistantMessage` 수신 시 | SDK 실행 완전 종료를 보장하는 신호. 중간 저장 시 불완전 세션 위험 |
| session_id None 처리 | 경고 로그 + 기존 동작 유지 | 에러 처리 | 세션 연속성 미작동은 기능 저하이지 생성 실패가 아님 |
| 프론트엔드 변경 | 없음 | 세션 상태 표시 추가 | 서버 내부 구현 세부사항을 클라이언트에 노출할 필요 없음 |
