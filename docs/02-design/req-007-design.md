# REQ-007 설계 문서 — AI 백엔드 선택 옵션

> Gate 2 — Architect 작성
> 담당 범위: REQ-007-01 ~ REQ-007-04

---

## 개요

- **REQ 그룹**: REQ-007 — AI 백엔드 선택 옵션
- **설계 방식**: 팩토리 패턴 (Factory Pattern) + 환경변수 기반 전략 선택
- **핵심 결정사항**: `AI_BACKEND` 환경변수 하나로 Anthropic API와 Claude Code SDK를 교체 가능하게 하며, 두 백엔드 모두 동일한 SSE 인터페이스를 준수하여 프론트엔드 코드는 변경하지 않는다.

### 설계 목표

| 목표 | 내용 |
|------|------|
| 프론트엔드 무변경 | SSE 이벤트 형식(item/done/error, text/patch/done/error)을 두 백엔드 모두 동일하게 유지 |
| 기존 서비스 최소 수정 | `ai_generate_service.py`, `chat_service.py`는 수정하지 않고, 라우터에서 팩토리를 통해 교체 |
| 단일 진입점 | 라우터가 팩토리를 통해 서비스를 가져오므로, 백엔드 전환은 `.env` 수정만으로 완결 |
| 확장 가능성 | 향후 세 번째 백엔드 추가 시 팩토리에 분기만 추가하면 되는 구조 |

---

## 시스템 구조

```
┌──────────────────────────────────────────────────────┐
│ 환경변수                                              │
│  AI_BACKEND=anthropic_api | claude_code_sdk          │
└──────────────────────┬───────────────────────────────┘
                       │ 읽기 (앱 시작 시 또는 요청마다)
                       ▼
┌──────────────────────────────────────────────────────┐
│ ai_backend_factory.py                                │
│   get_ai_generate_service() → AIGenerateService      │
│                             → AIGenerateServiceSDK   │
│   get_chat_service()        → ChatService            │
│                             → ChatServiceSDK         │
└────────┬─────────────────────────┬───────────────────┘
         │                         │
         ▼                         ▼
┌────────────────┐       ┌─────────────────────┐
│ routers/       │       │ routers/             │
│ generate.py    │       │ chat.py              │
│ (변경 대상)    │       │ (변경 대상)          │
└────────┬───────┘       └──────────┬────────────┘
         │                          │
    팩토리 호출                팩토리 호출
         │                          │
   ┌─────▼──────────────────────────▼────┐
   │          서비스 인터페이스 계층      │
   │                                      │
   │  ┌─────────────────────────────┐     │
   │  │ anthropic_api 경로          │     │
   │  │  AiGenerateService          │     │
   │  │  ChatService                │     │
   │  └─────────────────────────────┘     │
   │                                      │
   │  ┌─────────────────────────────┐     │
   │  │ claude_code_sdk 경로        │     │
   │  │  AIGenerateServiceSDK       │     │
   │  │  ChatServiceSDK             │     │
   │  └─────────────────────────────┘     │
   └──────────────────────────────────────┘
         │                          │
         ▼                          ▼
   SSE 스트림                  SSE 스트림
   (동일 형식)                 (동일 형식)
```

### 데이터 흐름 (claude_code_sdk 경로)

```
라우터 → AIGenerateServiceSDK.generate_stream()
           → query(prompt, options) [claude-agent-sdk]
           → message 오브젝트 스트리밍
           → JSON 파싱 (기존 _find_obj_end 로직 재사용)
           → SSE item 이벤트 발행
           → state.set_detail() 저장
           → SSE done 이벤트 발행
```

---

## 모듈 구조

### 신규 파일

| 파일 경로 | 역할 |
|----------|------|
| `backend/app/services/ai_backend_factory.py` | 환경변수를 읽어 적절한 서비스 인스턴스를 반환하는 팩토리 |
| `backend/app/services/ai_generate_service_sdk.py` | claude-agent-sdk를 사용하는 상세요구사항 생성 서비스 |
| `backend/app/services/chat_service_sdk.py` | claude-agent-sdk를 사용하는 채팅 수정 서비스 |

### 변경 파일

| 파일 경로 | 변경 내용 | 변경 수준 |
|----------|----------|----------|
| `backend/app/routers/generate.py` | `AiGenerateService()` 직접 생성 → `get_ai_generate_service()` 팩토리 호출로 교체 | 최소 (1~2줄) |
| `backend/app/routers/chat.py` | `ChatService()` 직접 생성 → `get_chat_service()` 팩토리 호출로 교체 | 최소 (1~2줄) |
| `backend/.env` (또는 `.env.example`) | `AI_BACKEND` 환경변수 항목 추가 | 1줄 추가 |

### 불변 파일 (수정 금지)

| 파일 경로 | 이유 |
|----------|------|
| `backend/app/services/ai_generate_service.py` | 기존 Anthropic API 구현 — 팩토리가 그대로 반환하므로 수정 불필요 |
| `backend/app/services/chat_service.py` | 동일 이유 |
| `backend/app/state.py` | 세션 상태 공유 — 두 SDK 서비스 모두 동일하게 재사용 |
| `backend/app/models/requirement.py` | 데이터 모델 공유 — 변경 없음 |
| 프론트엔드 코드 전체 | SSE 인터페이스 동일 유지로 변경 불필요 |

---

## 모듈/컴포넌트 설계

### `ai_backend_factory.py`

- **책임**: `AI_BACKEND` 환경변수를 읽어 적절한 서비스 구현체를 생성하여 반환한다. 라우터가 서비스 구현체를 직접 import하지 않도록 의존성 역전을 제공한다.
- **인터페이스**:
  ```python
  def get_ai_generate_service() -> AiGenerateService | AIGenerateServiceSDK
  def get_chat_service() -> ChatService | ChatServiceSDK
  ```
- **환경변수**: `AI_BACKEND` — 값이 `"anthropic_api"`이면 기존 구현체, 그 외(기본값 `"claude_code_sdk"`)는 SDK 구현체 반환
- **제약**: 인식할 수 없는 값은 기본값(`claude_code_sdk`)으로 폴백하고, 경고 로그를 남긴다. 앱 기동 실패 원인이 되어서는 안 된다.
- **결정 근거**: 라우터에서 `if backend == ...` 분기를 반복하면 라우터가 비대해지고 테스트가 어려워진다. 팩토리를 별도 모듈로 격리하면 라우터는 인터페이스만 알고, 팩토리만 테스트하면 된다.

### `AIGenerateServiceSDK`

- **책임**: `claude-agent-sdk`의 `query()` API를 호출하여 상세요구사항을 생성하고, 기존 `AiGenerateService.generate_stream()`과 동일한 SSE 형식으로 스트리밍한다.
- **인터페이스**:
  ```python
  class AIGenerateServiceSDK:
      async def generate_stream(self, session_id: str) -> AsyncGenerator[str, None]
  ```
- **SSE 출력 형식**: 기존과 동일 — `item`, `done`, `error` 이벤트 타입을 동일한 JSON 구조로 발행
- **내부 흐름**:
  1. `state.get_original()` — 원본 요구사항 조회 (기존 state 재사용)
  2. 프롬프트 조립 — `ai_generate_service.py`의 `_SYSTEM_PROMPT`와 동일한 시스템 프롬프트를 공유 상수로 추출하여 재사용
  3. `query(prompt=full_prompt, options=ClaudeAgentOptions(allowed_tools=[]))` 호출
  4. 반환된 메시지 오브젝트에서 텍스트 추출 → 버퍼에 누적
  5. 기존 `_find_obj_end()` 로직(또는 동일 함수)으로 JSON 객체 경계 감지 → `item` 이벤트 발행
  6. `state.set_detail()` 저장 후 `done` 이벤트 발행
- **제약**:
  - `claude-agent-sdk`가 설치되지 않은 환경에서 `AIGenerateServiceSDK`를 인스턴스화하면 `ImportError`가 발생한다. 팩토리가 이를 포착하여 `503` 응답으로 변환해야 한다.
  - `query()` 호출은 `async for` 루프로 처리 — SDK가 메시지 오브젝트를 비동기 이터레이터로 반환한다.
  - 텍스트 추출 방식: `message.content` 우선, 없으면 `message.result` 사용 (참조 문서 방식 B 기준)
- **에러 처리**: SDK 예외 → `error` SSE 이벤트 발행. 기존 서비스와 동일한 에러 이벤트 형식.
- **결정 근거**: `_find_obj_end()` 같은 JSON 파싱 유틸리티는 `ai_generate_service.py`에서 모듈 수준 함수로 이미 존재한다. SDK 서비스가 이를 import하여 재사용하면 중복 구현을 피할 수 있다.

### `ChatServiceSDK`

- **책임**: `claude-agent-sdk`의 `query()` API를 호출하여 채팅 수정 요청을 처리하고, 기존 `ChatService.chat_stream()`과 동일한 SSE 형식으로 스트리밍한다.
- **인터페이스**:
  ```python
  class ChatServiceSDK:
      async def chat_stream(
          self,
          session_id: str,
          message: str,
          history: list[ChatMessage]
      ) -> AsyncGenerator[str, None]
  ```
- **SSE 출력 형식**: 기존과 동일 — `text`, `patch`, `done`, `error` 이벤트 타입과 PATCH 태그 프로토콜 그대로 유지
- **내부 흐름**:
  1. 서버 측 메시지 길이 검증 (2000자, `chat_service.py`의 `MAX_MESSAGE_LENGTH` 공유 상수 재사용)
  2. `state.get_detail()` — 현재 상세요구사항 조회
  3. 시스템 프롬프트 조립 — `chat_service.py`의 `_build_system_prompt()` 함수 재사용
  4. `history` + `message`를 단일 프롬프트 문자열로 직렬화하여 `query()` 전달
  5. SDK 반환 메시지에서 텍스트 추출 — 전체 응답을 `full_text`에 누적
  6. `chat_service.py`의 `_process_patches()` 함수 재사용하여 PATCH 태그 일괄 처리
  7. `done` 이벤트 발행
- **제약**:
  - `claude-agent-sdk`의 `query()`는 멀티턴 히스토리를 직접 지원하지 않을 수 있다. 히스토리는 시스템 프롬프트에 직렬화하거나 단일 프롬프트에 포함하는 방식으로 우회한다. 실제 SDK API 시그니처 확인 후 조정 필요.
  - 스트리밍 중간 텍스트 발행: SDK가 토큰 단위 스트리밍을 지원하면 실시간 `text` 이벤트 발행, 지원하지 않으면 전체 응답 완료 후 일괄 발행. 두 경우 모두 `patch` 이벤트는 완료 후 일괄 처리.
- **에러 처리**: SDK 예외 → `error` SSE 이벤트. `MAX_MESSAGE_LENGTH` 초과 → `error` 이벤트 (기존과 동일).

### 유틸리티 함수 공유 전략

아래 함수들은 `ai_generate_service.py`와 `chat_service.py` 내부에 이미 구현되어 있다. SDK 서비스에서 직접 import하여 재사용하고, 중복 구현을 방지한다.

| 함수 | 위치 | 재사용 대상 |
|------|------|------------|
| `_find_obj_end()` | `ai_generate_service.py` | `AIGenerateServiceSDK` |
| `_parse_obj()` | `ai_generate_service.py` | `AIGenerateServiceSDK` |
| `_process_patches()` | `chat_service.py` | `ChatServiceSDK` |
| `_build_system_prompt()` | `chat_service.py` | `ChatServiceSDK` |
| `_SYSTEM_PROMPT` 상수 | `ai_generate_service.py` | `AIGenerateServiceSDK` |
| `MAX_MESSAGE_LENGTH` 상수 | `chat_service.py` | `ChatServiceSDK` |
| `_sse()` | 양쪽 모두 | 각 SDK 서비스가 자체 보유 (2줄짜리 유틸이므로 공유보다 자체 정의가 단순) |

---

## 디렉토리 구조

```
backend/
├── .env                                  # AI_BACKEND 환경변수 추가
├── app/
│   ├── routers/
│   │   ├── generate.py                   # [변경] 팩토리 호출로 교체
│   │   └── chat.py                       # [변경] 팩토리 호출로 교체
│   └── services/
│       ├── ai_generate_service.py        # [불변] 기존 Anthropic API 구현
│       ├── chat_service.py               # [불변] 기존 Anthropic API 구현
│       ├── ai_backend_factory.py         # [신규] 팩토리
│       ├── ai_generate_service_sdk.py    # [신규] SDK 구현
│       └── chat_service_sdk.py           # [신규] SDK 구현
```

---

## 환경변수 설정

### `.env` 추가 항목

```bash
# AI 백엔드 선택
# claude_code_sdk: Claude Code SDK 사용 (claude-agent-sdk 설치 + Claude.ai 로그인 필요) — 기본값
# anthropic_api: 기존 Anthropic API 사용 (ANTHROPIC_API_KEY 필요)
AI_BACKEND=claude_code_sdk
```

### 백엔드별 사전 조건

| 항목 | anthropic_api | claude_code_sdk |
|------|--------------|-----------------|
| 환경변수 | `ANTHROPIC_API_KEY` 필수 | 불필요 |
| 패키지 | `anthropic` (기존) | `claude-agent-sdk` 추가 설치 |
| 인증 방식 | API 키 | `~/.claude/.credentials.json` (Claude.ai OAuth) |
| 서버 요구사항 | 없음 | Claude.ai Pro/Max 구독 + 로그인 세션 유지 |

### `.env.example` 업데이트 내용

기존 `ANTHROPIC_API_KEY` 항목 아래에 `AI_BACKEND` 항목을 추가한다.

---

## API 설계

REQ-007은 기존 API 엔드포인트를 신규 추가하지 않는다. 기존 엔드포인트의 내부 구현을 교체하는 방식이다.

| Method | Path | 변경 내용 | 비고 |
|--------|------|---------|------|
| POST | `/api/v1/generate` | 서비스 생성 방식 변경 (팩토리 경유) | SSE 형식 동일 유지 |
| POST | `/api/v1/chat` | 서비스 생성 방식 변경 (팩토리 경유) | SSE 형식 동일 유지 |

### SSE 인터페이스 동일성 보장

두 백엔드 모두 아래 SSE 형식을 정확히 준수해야 한다. 프론트엔드는 `AI_BACKEND` 값을 알지 못하며 알 필요도 없다.

**generate 엔드포인트 SSE:**
```
data: {"type": "item", "data": {"id": "...", "parent_id": "...", "category": "...", "name": "...", "content": "...", "order_index": 0, "is_modified": false}}
data: {"type": "done", "total": 12}
data: {"type": "error", "message": "..."}
```

**chat 엔드포인트 SSE:**
```
data: {"type": "text", "delta": "..."}
data: {"type": "patch", "id": "REQ-001-02", "field": "content", "value": "..."}
data: {"type": "done"}
data: {"type": "error", "message": "..."}
```

---

## 단위 테스트 ID 사전 할당

| UT-ID | 대상 | 설명 | REQ-ID |
|-------|------|------|--------|
| UT-007-01 | `get_ai_generate_service()` | `AI_BACKEND=anthropic_api` → `AiGenerateService` 인스턴스 반환 | REQ-007-01 |
| UT-007-02 | `get_ai_generate_service()` | `AI_BACKEND=claude_code_sdk` → `AIGenerateServiceSDK` 인스턴스 반환 | REQ-007-01 |
| UT-007-03 | `get_ai_generate_service()` | `AI_BACKEND` 미설정(기본값) → `AIGenerateServiceSDK` 인스턴스 반환 | REQ-007-04 |
| UT-007-04 | `get_ai_generate_service()` | `AI_BACKEND=invalid_value` → `AIGenerateServiceSDK` 폴백 반환 (앱 크래시 없음) | REQ-007-04 |
| UT-007-05 | `get_chat_service()` | `AI_BACKEND=anthropic_api` → `ChatService` 인스턴스 반환 | REQ-007-01 |
| UT-007-06 | `get_chat_service()` | `AI_BACKEND=claude_code_sdk` → `ChatServiceSDK` 인스턴스 반환 | REQ-007-01 |
| UT-007-07 | `AIGenerateServiceSDK.generate_stream()` | SDK 정상 응답 → `item` 이벤트 1건 이상 발행 | REQ-007-02 |
| UT-007-08 | `AIGenerateServiceSDK.generate_stream()` | SSE `item` 이벤트 구조가 `AiGenerateService`와 동일한 JSON 키를 포함 | REQ-007-04 |
| UT-007-09 | `AIGenerateServiceSDK.generate_stream()` | SDK 예외 발생 → `error` SSE 이벤트 발행 (앱 크래시 없음) | REQ-007-02 |
| UT-007-10 | `AIGenerateServiceSDK.generate_stream()` | 원본 요구사항 없을 때 → `error` SSE 이벤트 발행 | REQ-007-02 |
| UT-007-11 | `ChatServiceSDK.chat_stream()` | SDK 정상 응답 → `text` 이벤트 발행 | REQ-007-03 |
| UT-007-12 | `ChatServiceSDK.chat_stream()` | SDK 응답에 PATCH 태그 포함 → `patch` 이벤트 발행 + state 업데이트 | REQ-007-03 |
| UT-007-13 | `ChatServiceSDK.chat_stream()` | 메시지 2000자 초과 → `error` 이벤트 발행 (SEC-007-02 연계) | REQ-007-03 |
| UT-007-14 | `ChatServiceSDK.chat_stream()` | SSE 이벤트 구조가 `ChatService`와 동일한 JSON 키를 포함 | REQ-007-04 |
| UT-007-15 | `routers/generate.py` | 팩토리 반환 서비스의 `generate_stream()` 호출 여부 | REQ-007-01 |
| UT-007-16 | `routers/chat.py` | 팩토리 반환 서비스의 `chat_stream()` 호출 여부 | REQ-007-01 |

---

## 보안 고려사항

| SEC-ID | 위협 | 대응 방안 | OWASP |
|--------|------|----------|-------|
| SEC-007-01 | `claude-agent-sdk` 미설치 환경에서 SDK 경로 호출 시 `ImportError` 노출 | 팩토리에서 `ImportError` 포착 → 503 응답 (내부 스택트레이스 클라이언트 미노출) | A05 Security Misconfiguration |
| SEC-007-02 | 채팅 입력 길이 제한 우회 — SDK 경로에서 검증 누락 가능성 | `ChatServiceSDK`에서도 `MAX_MESSAGE_LENGTH` 검증을 `chat_service.py`와 동일하게 적용 (공유 상수 재사용) | A03 Injection |
| SEC-007-03 | `AI_BACKEND` 환경변수 값 노출 — 설정 정보가 API 응답에 포함되면 공격자가 백엔드 유형 파악 가능 | 팩토리 폴백 로그는 서버 측 로그에만 기록, 클라이언트 응답에 백엔드 유형 포함 금지 | A02 Cryptographic Failures |
| SEC-007-04 | `~/.claude/.credentials.json` 자격증명 파일 유출 | 서버 디렉토리 접근 제어 — 웹 루트에서 `~/.claude/` 접근 불가하도록 배포 설정 확인 | A01 Broken Access Control |
| SEC-007-05 | 프롬프트 인젝션 — SDK 경로에서 원본 요구사항 content를 raw 문자열로 프롬프트에 삽입 시 위험 | `AIGenerateServiceSDK`에서도 원본 요구사항을 JSON 직렬화하여 전달 (SEC-002-02 동일 원칙 적용) | A03 Injection |
| SEC-007-06 | SDK 동시 요청 과다 — `claude-agent-sdk`는 subprocess 기반이므로 다수 동시 요청 시 리소스 고갈 가능 | 단기적으로 요청 큐 또는 세마포어로 동시 SDK 호출 수 제한 (로컬 단일 사용자 환경에서는 낮은 위험) | A05 Security Misconfiguration |

---

## 영향 받는 기존 파일 목록

| 파일 | 변경 유형 | 변경 내용 요약 |
|------|----------|--------------|
| `backend/app/routers/generate.py` | 수정 | `AiGenerateService()` → `get_ai_generate_service()` 교체, import 추가 |
| `backend/app/routers/chat.py` | 수정 | `ChatService()` → `get_chat_service()` 교체, import 추가 |
| `backend/.env` (또는 `.env.example`) | 수정 | `AI_BACKEND=claude_code_sdk` 항목 추가 |

### 영향받지 않는 파일 (확인 완료)

| 파일 | 이유 |
|------|------|
| `backend/app/services/ai_generate_service.py` | 팩토리가 기존 클래스를 그대로 반환 — 내부 수정 없음 |
| `backend/app/services/chat_service.py` | 동일 이유 |
| `backend/app/state.py` | 두 SDK 서비스 모두 동일 state API 사용 |
| `backend/app/models/requirement.py` | 데이터 모델 공유 — 변경 없음 |
| `backend/app/models/api.py` | 요청 스키마 변경 없음 |
| 프론트엔드 전체 (`frontend/`) | SSE 인터페이스 동일 유지 |

---

## 트레이드오프 기록

| 결정 | 선택한 방식 | 대안 | 이유 |
|------|------------|------|------|
| 백엔드 전환 방식 | 환경변수 + 재기동 | 런타임 API 전환 | 런타임 전환은 세션 중 요청 순서 보장이 복잡해짐. 단일 사용자 도구이므로 재기동 수용 가능 |
| 팩토리 위치 | `services/ai_backend_factory.py` | 라우터 내 인라인 분기 | 라우터 단일 책임 원칙 유지, 팩토리만 테스트하면 됨 |
| 유틸 함수 공유 | 기존 파일에서 import | 별도 `utils.py`로 추출 | 기존 파일 수정 최소화 원칙. 함수 수가 적어 별도 모듈 불필요 |
| 히스토리 전달 (SDK) | 단일 프롬프트로 직렬화 | SDK 멀티턴 지원 | SDK의 멀티턴 API 미확인 상태. 프롬프트 직렬화가 가장 안전한 기본 접근 |
| 스트리밍 방식 | 응답 완료 후 일괄 처리 우선 | 토큰 단위 실시간 스트리밍 | SDK의 토큰 스트리밍 API 미확인. 기능 동작 확보 후 실시간 스트리밍으로 개선 가능 |
