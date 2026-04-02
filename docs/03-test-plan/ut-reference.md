# 단위 테스트 참조 (UT-ID)

> UT-ID는 설계 문서에서 사전 할당. Developer가 구현 시 작성·실행하며, QA는 Gate 4에서 전수 Pass 여부만 확인한다.

| UT-ID | REQ-ID | 대상 | 설명 | Developer 실행 결과 |
|-------|--------|------|------|-------------------|
| UT-001-01 | REQ-001-02 | `HwpProcessor.process()` | 정상 HWP → OriginalRequirement 리스트 반환, 4개 필드 모두 비어있지 않음 | PASS (2026-04-01, 10/10) |
| UT-001-02 | REQ-001-04 | `HwpProcessor.process()` | 비 HWP 파일 경로 → ValueError 발생 | PASS (2026-04-01, 10/10) |
| UT-001-03 | REQ-001-01 | `HwpParseService.parse()` | 정상 바이트 → ParseResult 반환, session_id 포함 | PASS (2026-04-01, 10/10) |
| UT-001-04 | REQ-001-04 | `HwpParseService.parse()` | .docx 파일 → INVALID_FILE_TYPE 예외 | PASS (2026-04-01, 10/10) |
| UT-001-05 | REQ-006-03 | 임시 파일 삭제 | 파싱 완료/실패 후 tmp 파일 미존재 확인 | PASS (2026-04-01, 10/10) |
| UT-002-01 | REQ-002-01 | `AiGenerateService.generate_stream()` | 정상 세션 → item 이벤트 1건 이상 발행 | PASS (2026-04-01, test_generate.py) |
| UT-002-02 | REQ-002-04 | `AiGenerateService.generate_stream()` | Claude APIError → error 이벤트 발행 | PASS (2026-04-01, test_generate.py) |
| UT-002-03 | REQ-002-02 | 1:N 구조 | 각 parent_id에 1개 이상 DetailRequirement 생성 | PASS (2026-04-01, test_generate.py) |
| UT-002-04 | REQ-002-02 | ID 채번 | `{parent_id}-{NN}` 형식 준수, 중복 없음 | PASS (2026-04-01, test_generate.py) |
| UT-003-01 | REQ-003-01 | `OriginalReqTable` | rows 5건 → 테이블 행 5개 렌더링 | PASS (2026-04-01, original-table.test.tsx) |
| UT-003-02 | REQ-003-02 | `DetailReqTable` | `appendDetailReq()` 3회 → 행 3개 추가 | PASS (2026-04-01, detail-table.test.tsx) |
| UT-003-03 | REQ-003-03 | `InlineEditCell` | 셀 클릭 → input 렌더링, blur → `patchDetailReq` 호출 | PASS (2026-04-01, detail-table.test.tsx) |
| UT-003-04 | REQ-003-04 | 시각 구분 | 원본/상세 행 배경색 CSS 클래스 올바른 적용 | PASS (2026-04-01, detail-table.test.tsx) |
| UT-003-05 | REQ-003-04 | 수정 하이라이트 | patch 이벤트 수신 → 해당 행 강조 CSS 적용 | PASS (2026-04-01, chat-panel.test.tsx) |
| UT-004-01 | REQ-004-01 | `ChatService.chat_stream()` | 정상 요청 → text/patch 이벤트 발행 | PASS (2026-04-01, test_chat.py) |
| UT-004-02 | REQ-004-02 | patch 파싱 | `<PATCH>{...}</PATCH>` 태그 → patch 이벤트 + 스토어 업데이트 | PASS (2026-04-01, test_chat.py + chat-panel.test.tsx) |
| UT-004-03 | REQ-004-03 | `ChatPanel` | 메시지 전송 → chatHistory에 user 메시지 추가 | PASS (2026-04-01, chat-panel.test.tsx) |
| UT-004-04 | REQ-004-01 | 컨텍스트 전달 | 현재 detailReqs 전체가 시스템 프롬프트에 포함 | PASS (2026-04-01, test_chat.py) |
| UT-004-05 | REQ-004-01 | 채팅 비활성화 | detailReqs 비어있을 때 ChatInput disabled | PASS (2026-04-01, chat-panel.test.tsx) |
| UT-005-01 | REQ-005-01 | `ExcelExportService.export(stage=1)` | 4컬럼 xlsx, 원본 행 수 일치 | PASS (2026-04-01, test_excel.py) |
| UT-005-02 | REQ-005-02 | `ExcelExportService.export(stage=2)` | 6컬럼 xlsx, 원본+상세 인터리빙 순서 확인 | PASS (2026-04-01, test_excel.py) |
| UT-005-03 | REQ-005-01 | `GET /api/v1/download` | Content-Type xlsx 헤더 확인 | PASS (2026-04-01, test_excel.py) |
| UT-005-04 | REQ-005-02 | 수정 반영 | `is_modified=True` 행 → 2단계 엑셀에 수정값 포함 | PASS (2026-04-01, test_excel.py) |
| UT-005-05 | REQ-005-02 | stage=2 미생성 | detailReqs 없을 때 422 반환 | PASS (2026-04-01, test_excel.py) |
| UT-006-01 | REQ-006-01 | CORS | `localhost:3000` → 200, `localhost:9999` → 403 | PASS (2026-04-01, main.py 소스 확인) |
| UT-006-02 | REQ-006-02 | 파서 재활용 | `HWPOLEReader`, `HwpBodyParser` import 성공, 수정 없음 확인 | PASS (2026-04-01, 4/4) |
| UT-006-03 | REQ-006-04 | `SessionStore` | 저장/조회/reset 정상 동작 | PASS (2026-04-01, 10/10) |
| UT-006-04 | REQ-006-04 | 세션 연속성 | upload → generate → chat → download가 동일 session_id 사용 | PASS (2026-04-01, test_foundation.py + store.test.ts) |
| UT-007-01 | REQ-007-01 | `get_ai_generate_service()` | `AI_BACKEND=anthropic_api` → `AiGenerateService` 인스턴스 반환 | PASS (2026-04-01, test_factory.py) |
| UT-007-02 | REQ-007-01 | `get_ai_generate_service()` | `AI_BACKEND=claude_code_sdk` → `AIGenerateServiceSDK` 인스턴스 반환 | PASS (2026-04-01, test_factory.py) |
| UT-007-03 | REQ-007-04 | `get_ai_generate_service()` | `AI_BACKEND` 미설정(기본값) → `AIGenerateServiceSDK` 인스턴스 반환 | PASS (2026-04-01, test_factory.py) |
| UT-007-04 | REQ-007-04 | `get_ai_generate_service()` | `AI_BACKEND=invalid_value` → `AIGenerateServiceSDK` 폴백 반환 (앱 크래시 없음) | PASS (2026-04-01, test_factory.py) |
| UT-007-05 | REQ-007-01 | `get_chat_service()` | `AI_BACKEND=anthropic_api` → `ChatService` 인스턴스 반환 | PASS (2026-04-01, test_factory.py) |
| UT-007-06 | REQ-007-01 | `get_chat_service()` | `AI_BACKEND=claude_code_sdk` → `ChatServiceSDK` 인스턴스 반환 | PASS (2026-04-01, test_factory.py) |
| UT-007-07 | REQ-007-02 | `AIGenerateServiceSDK.generate_stream()` | SDK mock 정상 응답 → `item` 이벤트 1건 이상 발행 | PASS (2026-04-01, test_sdk_services.py) |
| UT-007-08 | REQ-007-04 | `AIGenerateServiceSDK.generate_stream()` | SSE `item` 이벤트 구조가 `AiGenerateService`와 동일한 JSON 키를 포함 | PASS (2026-04-01, test_sdk_services.py) |
| UT-007-09 | REQ-007-02 | `AIGenerateServiceSDK.generate_stream()` | SDK 예외 발생 → `error` SSE 이벤트 발행 (앱 크래시 없음) | PASS (2026-04-01, test_sdk_services.py) |
| UT-007-10 | REQ-007-02 | `AIGenerateServiceSDK.generate_stream()` | 원본 요구사항 없을 때 → `error` SSE 이벤트 발행 | PASS (2026-04-01, test_sdk_services.py) |
| UT-007-11 | REQ-007-03 | `ChatServiceSDK.chat_stream()` | SDK mock 정상 응답 → `text` 이벤트 발행 | PASS (2026-04-01, test_sdk_services.py) |
| UT-007-12 | REQ-007-03 | `ChatServiceSDK.chat_stream()` | SDK 응답에 PATCH 태그 포함 → `patch` 이벤트 발행 + state 업데이트 | PASS (2026-04-01, test_sdk_services.py) |
| UT-007-13 | REQ-007-03 | `ChatServiceSDK.chat_stream()` | 메시지 2000자 초과 → `error` 이벤트 발행 (SEC-007-02 연계) | PASS (2026-04-01, test_sdk_services.py) |
| UT-007-14 | REQ-007-04 | `ChatServiceSDK.chat_stream()` | SSE 이벤트 구조가 `ChatService`와 동일한 JSON 키를 포함 | PASS (2026-04-01, test_sdk_services.py) |
| UT-007-15 | REQ-007-01 | `routers/generate.py` | 팩토리 반환 서비스의 `generate_stream()` 호출 여부 | PASS (2026-04-01, test_factory.py) |
| UT-007-16 | REQ-007-01 | `routers/chat.py` | 팩토리 반환 서비스의 `chat_stream()` 호출 여부 | PASS (2026-04-01, test_factory.py) |
| UT-008-01 | REQ-008-01 | `PATCH /api/v1/detail/{id}` | 유효한 id와 field로 요청 시 수정된 `DetailRequirement` 반환 (200) | (구현 후 업데이트) |
| UT-008-02 | REQ-008-01 | `PATCH /api/v1/detail/{id}` | 존재하지 않는 id로 요청 시 404 반환 | (구현 후 업데이트) |
| UT-008-03 | REQ-008-01 | `PATCH /api/v1/detail/{id}` | `field` 값이 허용 범위 외이면 422 반환 | (구현 후 업데이트) |
| UT-008-04 | REQ-008-03 | `PATCH /api/v1/detail/{id}` | 수정 후 `state.get_detail()` 목록에서 해당 항목 값이 변경되어 있음 | (구현 후 업데이트) |
| UT-008-05 | REQ-008-01 | `PATCH /api/v1/detail/{id}` | 수정 후 해당 항목의 `is_modified`가 `true`로 설정됨 | (구현 후 업데이트) |
| UT-008-06 | REQ-008-02 | `patchDetailReq()` (프론트엔드 api) | 정상 응답 시 `DetailRequirement` 객체를 반환함 | (구현 후 업데이트) |
| UT-008-07 | REQ-008-02 | `patchDetailReq()` (프론트엔드 api) | 서버 404 응답 시 예외를 throw함 | (구현 후 업데이트) |
| UT-008-08 | REQ-008-02, REQ-008-03 | `useAppStore.patchDetailReq` (또는 sync 헬퍼) | API 성공 후 Zustand 스토어의 해당 항목 field 값이 갱신됨 | (구현 후 업데이트) |
| UT-008-09 | REQ-008-02 | `useAppStore.patchDetailReq` (또는 sync 헬퍼) | API 실패 시 스토어 값은 변경되지 않고 에러 상태가 설정됨 | (구현 후 업데이트) |
| UT-009-01 | REQ-009-01 | `AIGenerateServiceSDK.generate_stream()` | 생성 완료 후 `state.get_sdk_session_id()`에 SDK session_id가 저장됨 | (구현 후 업데이트) |
| UT-009-02 | REQ-009-01 | `AIGenerateServiceSDK.generate_stream()` | `ResultMessage.session_id`가 None인 경우 state 저장 없이 스트림이 정상 완료됨 | (구현 후 업데이트) |
| UT-009-03 | REQ-009-02 | `ChatServiceSDK.chat_stream()` | `state.get_sdk_session_id()`가 None이면 `resume` 없이 `query()` 호출됨 | (구현 후 업데이트) |
| UT-009-04 | REQ-009-02 | `ChatServiceSDK.chat_stream()` | `state.get_sdk_session_id()`가 유효한 값이면 `ClaudeAgentOptions(resume=session_id)`로 `query()` 호출됨 | (구현 후 업데이트) |
| UT-009-05 | REQ-009-03 | `state.reset_session()` | 호출 후 `state.get_sdk_session_id()`가 `None`을 반환함 | (구현 후 업데이트) |
| UT-009-06 | REQ-009-01 | `state.set_sdk_session_id()` / `get_sdk_session_id()` | 저장한 값이 조회 시 동일하게 반환됨 | (구현 후 업데이트) |
| UT-009-07 | REQ-009-03 | `SessionState` | `sdk_session_id` 필드의 기본값이 `None`임 | (구현 후 업데이트) |
