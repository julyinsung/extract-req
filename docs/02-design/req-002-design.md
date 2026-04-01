# REQ-002 설계 — AI 상세요구사항 자동 생성

> Gate 2a — 담당 범위: REQ-002-01 ~ REQ-002-04

---

## API 엔드포인트

| Method | Path | 설명 | 요청 바디 | 응답 |
|--------|------|------|----------|------|
| POST | `/api/v1/generate` | 상세요구사항 AI 생성 (SSE 스트리밍) | `{"session_id": "..."}` | SSE 스트림 |

### SSE 이벤트 형식

```
data: {"type": "item", "data": {"id": "REQ-001-01", "parent_id": "REQ-001", "category": "기능", "name": "파일 선택 UI", "content": "..."}}

data: {"type": "item", "data": {...}}

data: {"type": "done", "total": 12}

data: {"type": "error", "message": "Claude API 호출 실패"}
```

### 에러 응답

| HTTP | 코드 | 상황 |
|------|------|------|
| 404 | `SESSION_NOT_FOUND` | 세션 없음 또는 파싱 미완료 |
| 503 | `AI_UNAVAILABLE` | Claude API 접속 불가 |

---

## 백엔드 모듈

### `app/services/ai_generate_service.py`

```python
class AiGenerateService:
    async def generate_stream(self, session_id: str) -> AsyncGenerator[str, None]:
        """원본 요구사항 → Claude API → DetailRequirement SSE 스트리밍."""
```

내부 흐름:
1. `SessionStore.get_original(session_id)` — 원본 요구사항 조회
2. 프롬프트 조립 (시스템 + 원본 JSON 직렬화)
3. `anthropic.messages.stream()` 호출
4. 스트리밍 청크 누적 → 완전한 JSON 객체 경계(`}`) 감지 시 파싱
5. `item` SSE 이벤트 발행
6. 완료 시 `SessionStore.set_detail(session_id, details)` 저장
7. `done` SSE 이벤트 발행
8. 예외: `anthropic.APIError`, `anthropic.RateLimitError` → `error` SSE 이벤트

---

## Claude API 프롬프트 전략

### 시스템 프롬프트

```
당신은 공공/기업 제안 업무 전문가입니다.
주어진 원본 요구사항을 구현 가능한 상세요구사항으로 분해하세요.

출력 규칙:
- JSON 배열만 반환 (마크다운 코드 블록, 설명 텍스트 없이 순수 JSON)
- 각 항목: {"id": "...", "parent_id": "...", "category": "...", "name": "...", "content": "..."}
- 원본 ID가 "SFR-001"이면 상세 ID는 "SFR-001-01", "SFR-001-02" ...
- 원본 1건당 2~5개의 구현 단위로 분해
```

### 사용자 메시지

```
다음 원본 요구사항 목록을 상세요구사항으로 분해해주세요.
[원본 요구사항 JSON 배열]
```

### ID 채번 규칙

```
parent_id = "SFR-001"
첫 번째 상세 → id = "SFR-001-01"
두 번째 상세 → id = "SFR-001-02"
N번째 상세  → id = "SFR-001-{N:02d}"
```

AI 응답에 ID가 누락/형식 불일치 시, 서버에서 parent_id + 시퀀스로 재생성.

---

## 데이터 모델

```python
# app/models/requirement.py

class DetailRequirement(BaseModel):
    id: str              # 예: "SFR-001-01"
    parent_id: str       # 예: "SFR-001"
    category: str        # 분류
    name: str            # 상세 요구사항 명칭
    content: str         # 상세 요구사항 내용
    order_index: int     # 동일 parent 내 순서 (0-based)
    is_modified: bool = False  # 채팅/인라인편집 수정 여부 (UI 강조용)
```

---

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-002-01 | `AiGenerateService.generate_stream()` | 정상 세션 → item 이벤트 1건 이상 발행 |
| UT-002-02 | `AiGenerateService.generate_stream()` | Claude APIError → error 이벤트 발행 |
| UT-002-03 | 1:N 구조 | 각 parent_id에 1개 이상 DetailRequirement 생성 |
| UT-002-04 | ID 채번 | `{parent_id}-{NN}` 형식 준수, 중복 없음 |

---

## SEC-ID

| SEC-ID | 내용 |
|--------|------|
| SEC-002-01 | `ANTHROPIC_API_KEY` 환경변수 관리, 코드 하드코딩 금지 |
| SEC-002-02 | 프롬프트 인젝션 방지 — 원본 요구사항 content를 JSON 직렬화하여 전달 (raw 문자열 삽입 금지) |
