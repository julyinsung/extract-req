# REQ-004 설계 — 채팅 기반 AI 수정

> Gate 2a — 담당 범위: REQ-004-01 ~ REQ-004-03

---

## API 엔드포인트

| Method | Path | 설명 | 요청 바디 | 응답 |
|--------|------|------|----------|------|
| POST | `/api/v1/chat` | 채팅 수정 요청 (SSE 스트리밍) | `ChatRequest` JSON | SSE 스트림 |

### 요청 스키마

```json
{
  "session_id": "uuid-v4-string",
  "message": "REQ-001-02의 내용을 더 구체적으로 작성해줘",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

채팅 히스토리는 **클라이언트가 유지**하고 매 요청 시 전송 — 서버는 히스토리를 저장하지 않음.

### SSE 이벤트 형식

```
data: {"type": "text", "delta": "네, REQ-001-02의 내용을 수정했습니다."}

data: {"type": "patch", "id": "REQ-001-02", "field": "content", "value": "수정된 상세 내용..."}

data: {"type": "done"}

data: {"type": "error", "message": "..."}
```

### PATCH 태그 프로토콜

Claude 응답 스트림에서 수정 명령과 채팅 텍스트를 구분하기 위해 태그 사용:

```
<PATCH>{"id":"REQ-001-02","field":"content","value":"새 내용"}</PATCH>
```

- `<PATCH>` 감지 시 → `patch` SSE 이벤트 발행 + `SessionStore.patch_detail()` 호출
- 나머지 텍스트 → `text` SSE 이벤트 발행 (채팅창 표시)
- 수정 대상 없는 일반 질문 → PATCH 태그 없이 `text` 이벤트만

---

## 백엔드 모듈

### `app/services/chat_service.py`

```python
class ChatService:
    async def chat_stream(
        self,
        session_id: str,
        message: str,
        history: list[ChatMessage]
    ) -> AsyncGenerator[str, None]:
        """채팅 메시지 + 컨텍스트 → Claude API → SSE 스트리밍."""
```

내부 흐름:
1. `SessionStore.get_detail(session_id)` — 현재 상세요구사항 전체 조회
2. 시스템 프롬프트 조립 (현재 상세요구사항 JSON 컨텍스트 포함)
3. `history` + 현재 `message`를 Claude `messages` 파라미터에 전달
4. 스트리밍 응답에서 `<PATCH>` 태그 감지 → `patch` 이벤트 발행 + `SessionStore.patch_detail()` 호출
5. 나머지 텍스트 → `text` 이벤트 발행
6. 완료 → `done` 이벤트

### 채팅 프롬프트 전략

**시스템 프롬프트:**
```
당신은 요구사항 분석 전문가입니다.
현재 상세요구사항 목록:
[DetailRequirement JSON 배열]

수정 요청 시 두 가지를 함께 반환하세요:
1. 채팅 응답 텍스트 (설명)
2. 수정 명령: <PATCH>{"id":"...","field":"name|content|category","value":"..."}</PATCH>

수정 없는 일반 질문은 PATCH 태그 없이 텍스트만 반환하세요.
```

---

## React 컴포넌트

### `ChatPanel`

```typescript
// 스토어 직접 접근
// useAppStore에서: chatHistory, isChatting, sessionId, detailReqs
```

- `sessionId`가 없거나 `detailReqs`가 비어 있을 때 입력창 비활성화
- `isChatting` 동안 재전송 방지
- 메시지 전송 후 최신 메시지로 자동 스크롤

### `ChatMessage`

```typescript
interface ChatMessageProps {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}
```

- user 메시지: 오른쪽 정렬, 파란 배경
- assistant 메시지: 왼쪽 정렬, 회색 배경

### `ChatInput`

- `Enter` 전송 (Shift+Enter 줄바꿈)
- 최대 2000자 제한 (SEC-004-02)
- 전송 중 버튼 비활성화

---

## 데이터 모델

```python
# app/models/requirement.py (서버 측 채팅 히스토리는 저장 안 함)

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    # timestamp는 클라이언트에서 관리
```

```typescript
// 프론트엔드 타입
interface ChatMessage {
  id: string          // uuid
  role: "user" | "assistant"
  content: string
  timestamp: Date
}
```

---

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-004-01 | `ChatService.chat_stream()` | 정상 요청 → text/patch 이벤트 발행 |
| UT-004-02 | patch 파싱 | `<PATCH>{...}</PATCH>` 태그 → `patch` 이벤트 + 스토어 업데이트 |
| UT-004-03 | `ChatPanel` | 메시지 전송 → chatHistory에 user 메시지 추가 |
| UT-004-04 | 컨텍스트 전달 | 현재 detailReqs 전체가 시스템 프롬프트에 포함 |
| UT-004-05 | 채팅 비활성화 | detailReqs 비어있을 때 ChatInput disabled |

---

## SEC-ID

| SEC-ID | 내용 |
|--------|------|
| SEC-004-01 | 채팅 입력 XSS 방지 (React 기본 이스케이프 + 서버 측 JSON 직렬화) |
| SEC-004-02 | 채팅 메시지 길이 제한 2000자 (클라이언트 + 서버 이중 검증) |
