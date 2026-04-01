# REQ-004 설계 — 채팅 기반 AI 수정

> 통합 설계 문서 참조: `req-all-design.md`

## 담당 범위

REQ-004-01 ~ REQ-004-03: 채팅 인터페이스, 수정 결과 테이블 반영, 대화 내역 유지

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/chat` | SSE 스트리밍 채팅 응답 |

응답 형식 (SSE):
```
event: text
data: {"delta": "REQ-001-02의 내용을 수정했습니다."}

event: patch
data: {"detail_id": "REQ-001-02", "field": "content", "value": "수정된 내용..."}

event: done
data: {}
```

`<PATCH>{...}</PATCH>` 태그로 채팅 텍스트와 테이블 수정 명령 구분.

## 서비스 모듈

- `ChatService.chat_stream(session_id, user_message)` — 현재 상세요구사항 컨텍스트 포함하여 Claude API 호출
- `SessionStore.patch_detail(session_id, detail_id, field, value)` — 수정 내용 반영

## React 컴포넌트

| 컴포넌트 | 역할 |
|---------|------|
| `ChatPanel` | 채팅 UI 전체 (입력창 + 대화 내역) |
| `ChatMessage` | 사용자/AI 메시지 버블 렌더링 |
| `ChatInput` | 텍스트 입력 + 전송 버튼 |

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-004-01 | `ChatService.chat_stream()` | user_message + 컨텍스트 → SSE 응답 |
| UT-004-02 | patch 이벤트 처리 | patch 수신 → detailReqs 상태 업데이트 |
| UT-004-03 | `ChatPanel` | 메시지 전송 → 대화 내역에 추가 |
| UT-004-04 | 컨텍스트 전달 | 현재 상세요구사항 전체가 프롬프트에 포함 |

## SEC-ID

| SEC-ID | 내용 |
|--------|------|
| SEC-004-01 | 채팅 입력 XSS 방지 (React 기본 이스케이프 + 서버 측 검증) |
| SEC-004-02 | 채팅 메시지 길이 제한 (최대 2000자) |
