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
| UT-010-01 | REQ-010-01 | `AiGenerateService.generate_stream()` | item 이벤트 직후 progress 이벤트가 발행되는지 확인 (current 1, total N) | (구현 후 업데이트) |
| UT-010-02 | REQ-010-01 | `AIGenerateServiceSDK.generate_stream()` | SDK 서비스도 동일한 progress 이벤트를 발행하는지 확인 | (구현 후 업데이트) |
| UT-010-03 | REQ-010-01 | `AiGenerateService.generate_stream()` | progress.current 값이 parent_id 완료 순서(1-based)와 일치하는지 확인 | (구현 후 업데이트) |
| UT-010-04 | REQ-010-02 | `DetailReqTable` | `isGenerating=true`, `progressTotal>0` 시 진행률 텍스트 "N / M 항목 생성 중" 렌더링 | (구현 후 업데이트) |
| UT-010-05 | REQ-010-03 | `DetailReqTable` | `isGenerating=false` 시 진행률 UI가 DOM에서 사라지는지 확인 | (구현 후 업데이트) |
| UT-011-01 | REQ-011-01 | `App` 레이아웃 | `#chat-area`에 `position: sticky` 스타일이 적용되어 있는지 확인 | (구현 후 업데이트) |
| UT-011-02 | REQ-011-02 | `ChatPanel` | sticky 상태에서 채팅 전송 버튼 클릭 → `handleSend` 호출되는지 확인 (기능 정상 동작) | (구현 후 업데이트) |
| UT-012-01 | REQ-012-02 | `state.delete_detail()` | 존재하는 id 삭제 시 True 반환 및 목록에서 제거 | (구현 후 업데이트) |
| UT-012-02 | REQ-012-02 | `state.delete_detail()` | 존재하지 않는 id 삭제 시 False 반환 | (구현 후 업데이트) |
| UT-012-03 | REQ-012-02 | `DELETE /api/v1/detail/{id}` | 존재하는 id 요청 시 200 + `{"deleted_id": id}` 반환 | (구현 후 업데이트) |
| UT-012-04 | REQ-012-02 | `DELETE /api/v1/detail/{id}` | 존재하지 않는 id 요청 시 404 반환 | (구현 후 업데이트) |
| UT-012-05 | REQ-012-03 | `DetailReqTable` | 삭제 버튼 클릭 → confirm 다이얼로그 표시 → 취소 시 행 유지 | (구현 후 업데이트) |
| UT-012-06 | REQ-012-01 | `DetailReqTable` | 삭제 버튼 클릭 → confirm 확인 시 해당 행 제거 | (구현 후 업데이트) |
| UT-012-07 | REQ-012-01 | `useAppStore.deleteDetailReq()` | API 성공 시 스토어에서 해당 id 제거 확인 | (구현 후 업데이트) |
| UT-012-08 | REQ-012-02 | `useAppStore.deleteDetailReq()` | API 404 실패 시 스토어 상태 불변 + error 설정 | (구현 후 업데이트) |
| UT-012-09 | REQ-012-01 | `DetailReqTable` | `isGenerating=true` 중 삭제 버튼 비활성화 확인 | (구현 후 업데이트) |
| UT-013-01 | REQ-013-01 | `snapshot.save_snapshot()` | 변경 후 `session_snapshot.json`이 생성되고 `original_requirements`와 `detail_requirements` 두 키를 포함함 | (구현 후 업데이트) |
| UT-013-02 | REQ-013-02 | `snapshot.save_snapshot()` | 두 번 연속 호출 시 파일이 최신 상태 1개로 덮어쓰임 (이전 데이터 잔존 없음) | (구현 후 업데이트) |
| UT-013-03 | REQ-013-03 | `snapshot.load_snapshot()` | 유효한 `session_snapshot.json` 존재 시 `state.get_detail()`이 복원된 항목을 반환함 | (구현 후 업데이트) |
| UT-013-04 | REQ-013-03 | `snapshot.load_snapshot()` | `session_snapshot.json`이 없으면 `False`를 반환하고 state가 빈 상태임 | (구현 후 업데이트) |
| UT-013-05 | REQ-013-03 | `snapshot.load_snapshot()` | `session_snapshot.json`이 손상된 JSON이면 `False`를 반환하고 서버 기동을 중단하지 않음 | (구현 후 업데이트) |
| UT-013-06 | REQ-013-01 | `state.patch_detail()` | 수정 성공 후 `session_snapshot.json`의 해당 항목 필드가 갱신된 값으로 저장됨 | (구현 후 업데이트) |
| UT-013-07 | REQ-013-01 | `state.delete_detail()` | 존재하는 id 삭제 시 `True` 반환, 이후 `state.get_detail()`에 해당 항목이 없음 | (구현 후 업데이트) |
| UT-013-08 | REQ-013-01 | `state.delete_detail()` | 존재하지 않는 id 삭제 시 `False` 반환, state 변경 없음 | (구현 후 업데이트) |
| UT-013-09 | REQ-013-01 | `state.delete_detail()` | 삭제 성공 후 `session_snapshot.json`에 해당 항목이 포함되지 않음 | (구현 후 업데이트) |
| UT-013-10 | REQ-013-01 | `state.set_detail()` | 호출 후 `session_snapshot.json`의 `detail_requirements` 항목 수가 인메모리 state와 일치함 | (구현 후 업데이트) |
| UT-013-11 | REQ-013-04 | `snapshot.save_snapshot()` | 파일 쓰기 실패 시(권한 오류 등) 예외를 억제하고 호출자에게 전파하지 않음 | (구현 후 업데이트) |
| UT-013-12 | REQ-013-01 | `DELETE /api/v1/detail/{id}` | 존재하는 id로 DELETE 호출 시 200과 `{"deleted_id": id}` 반환 | (구현 후 업데이트) |
| UT-013-13 | REQ-013-01 | `DELETE /api/v1/detail/{id}` | 존재하지 않는 id로 DELETE 호출 시 404와 `NOT_FOUND` 에러 코드 반환 | (구현 후 업데이트) |
| UT-013-14 | REQ-013-03 | `snapshot.load_snapshot()` | 복원 후 `state.get_original()`이 스냅샷의 `original_requirements` 목록을 반환함 | (구현 후 업데이트) |
