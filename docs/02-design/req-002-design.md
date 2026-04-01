# REQ-002 설계 — AI 상세요구사항 자동 생성

> 통합 설계 문서 참조: `req-all-design.md`

## 담당 범위

REQ-002-01 ~ REQ-002-04: Claude API 호출, 1:N 생성, 로딩 표시, 오류 처리

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/generate` | SSE 스트리밍으로 상세요구사항 생성 |

응답 형식 (SSE):
```
event: item
data: {"detail_id": "REQ-001-01", "parent_id": "REQ-001", "category": "...", "name": "...", "content": "..."}

event: done
data: {"total": 12}

event: error
data: {"message": "Claude API 호출 실패"}
```

## 서비스 모듈

- `AiGenerateService.generate_stream(session_id)` — Claude API SSE 스트리밍
- 프롬프트 전략: 원본 요구사항 1건씩 순차 처리, JSON 배열로 응답 요청
- `SessionStore.save_details(session_id, details)` — 생성 결과 저장

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-002-01 | `AiGenerateService.generate_stream()` | 정상 응답 → DetailRequirement 리스트 반환 |
| UT-002-02 | `AiGenerateService.generate_stream()` | Claude API 오류 → error 이벤트 발행 |
| UT-002-03 | 1:N 구조 | 각 원본 REQ에 1개 이상 상세 REQ 생성 |
| UT-002-04 | ID 채번 | parent_id + 시퀀스로 고유 ID 보장 |

## SEC-ID

| SEC-ID | 내용 |
|--------|------|
| SEC-002-01 | Claude API 키 환경변수 관리 (코드 하드코딩 금지) |
| SEC-002-02 | 프롬프트 인젝션 방지 (사용자 입력 이스케이프 처리) |
