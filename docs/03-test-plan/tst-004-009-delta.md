# QA 테스트 케이스 — REQ-004 / REQ-009 추가 변경분 (Delta)

> 이 파일은 REQ-004-04/05/06 (REQ 그룹 컨텍스트 선택) 및 REQ-009-04 (그룹별 독립 session_id)에 대한 추가 테스트 케이스를 포함한다.
> 테스트 환경, 도구, 명령어는 ENVIRONMENT.md를 참조한다.
> TST-ID 채번은 tst-010-013.md 이후(TST-013-08 / TST-SEC-26)에 이어서 시작한다.

---

### REQ-004 (추가): 채팅 REQ 그룹 컨텍스트 선택

| TST-ID | REQ-ID | AC-ID | 테스트 유형 | 우선순위 | 시나리오 | 기대 결과 | 상태 | 증빙 |
|--------|--------|-------|-----------|---------|---------|----------|------|------|
| TST-004-04 | REQ-004-04 | AC-004-04 | E2E | Critical | **Given** 원본 요구사항 테이블과 채팅창이 화면에 표시되어 있고 원본 요구사항이 3건 이상 표시되어 있다. **When** 사용자가 원본 요구사항 테이블에서 `REQ-001` 행을 클릭한다. **Then** 채팅창 상단에 "REQ-001 컨텍스트로 대화 중" 문구가 표시되고, 이후 채팅 전송 시 요청 바디의 `req_group` 필드가 `"REQ-001"`로 전송된다. | 행 클릭 후 채팅창 헤더에 "REQ-001 컨텍스트로 대화 중" 표시. 다음 채팅 전송 시 `req_group: "REQ-001"` 포함 확인 | 미실행 | |
| TST-004-05 | REQ-004-04 | AC-004-04 | E2E | High | **Given** 채팅창이 `REQ-001` 컨텍스트로 설정되어 있다. **When** 사용자가 원본 요구사항 테이블에서 다른 행(`REQ-002`)을 클릭한다. **Then** 채팅창 상단 컨텍스트 표시가 "REQ-002 컨텍스트로 대화 중"으로 전환되고, 다음 채팅 전송 시 `req_group` 필드가 `"REQ-002"`로 변경된다. | 컨텍스트 전환 시 채팅창 헤더 갱신. 전송 `req_group` 값 갱신 | 미실행 | |
| TST-004-06 | REQ-004-05 | AC-004-05 | Integration | Critical | **Given** `AI_BACKEND=claude_code_sdk`로 설정되어 있고 원본 요구사항이 5건, 각 그룹의 상세항목이 총 25건 서버 state에 로드되어 있다. `ChatServiceSDK.chat_stream()` 내부의 `_build_system_prompt()` 호출이 mock 또는 캡처 가능한 상태이다. **When** `POST /api/v1/chat`에 `{ "req_group": "REQ-001", "message": "수정 요청", ... }` 형식으로 전송한다. **Then** `_build_system_prompt()`에 전달된 `filtered_details` 인자가 `parent_id == "REQ-001"`인 항목만 포함하고, 다른 그룹(`REQ-002` 등)의 상세항목은 포함하지 않는다. | 시스템 프롬프트 구성 시 `REQ-001` 상세항목만 포함. 다른 그룹 항목 미포함 | 미실행 | |
| TST-004-07 | REQ-004-05 | AC-004-05 | Integration | High | **Given** `AI_BACKEND=anthropic_api`로 설정되어 있고 원본 요구사항 3건, 각 그룹 상세항목이 총 15건 서버 state에 로드되어 있다. **When** `POST /api/v1/chat`에 `{ "req_group": "REQ-002", "message": "수정 요청", ... }` 형식으로 전송한다. **Then** Claude API에 전달된 시스템 프롬프트에 `REQ-002`의 원본 텍스트(1건)와 `parent_id == "REQ-002"`인 상세항목만 포함된다. 다른 그룹의 데이터는 포함되지 않는다. | anthropic_api 경로도 동일한 그룹 필터링 적용. 시스템 프롬프트 내 `REQ-002` 데이터만 포함 | 미실행 | |
| TST-004-08 | REQ-004-06 | AC-004-06 | Integration | Critical | **Given** `AI_BACKEND=claude_code_sdk`로 설정되어 있고 `query()` mock이 `<REPLACE>[{"name": "신규명", "content": "신규내용", "category": "기능"}]</REPLACE>` 형식의 응답을 반환하도록 설정되어 있다. **When** `POST /api/v1/chat`에 `{ "req_group": "REQ-001", "message": "전체 재작성해줘" }` 형식으로 전송한다. **Then** SSE 스트림에 `type: "replace"` 이벤트가 수신되고, 해당 이벤트의 `req_group`이 `"REQ-001"`이며, `items` 배열에 새 상세항목이 포함된다. 서버 state에서 `REQ-001`의 상세항목이 새 항목으로 교체된다. | `replace` SSE 이벤트 수신. `req_group == "REQ-001"`, `items` 배열 포함. 서버 state `REQ-001` 상세항목 교체 완료 | 미실행 | |
| TST-004-09 | REQ-004-06 | AC-004-06 | E2E | High | **Given** 상세요구사항 테이블에 `REQ-001`의 상세항목이 표시되어 있고 채팅창이 `REQ-001` 컨텍스트로 설정되어 있다. **When** `replace` SSE 이벤트가 수신된다. **Then** 테이블에서 `REQ-001` 그룹의 모든 기존 행이 제거되고, 이벤트의 `items`에 포함된 새 항목이 테이블에 즉시 표시된다. 교체된 행이 색상으로 시각적으로 구분된다. | `replace` 이벤트 수신 후 테이블 `REQ-001` 행 전체 교체. 교체 항목 강조 표시 | 미실행 | |

---

### REQ-009 (추가): REQ 그룹별 독립 session_id

| TST-ID | REQ-ID | AC-ID | 테스트 유형 | 우선순위 | 시나리오 | 기대 결과 | 상태 | 증빙 |
|--------|--------|-------|-----------|---------|---------|----------|------|------|
| TST-009-08 | REQ-009-04 | AC-009-04 | Integration | Critical | **Given** `AI_BACKEND=claude_code_sdk`로 설정되어 있고, `state.py`의 `sdk_sessions` 딕셔너리에 `"REQ-001": "sess-001-abc"`, `"REQ-002": "sess-002-xyz"` 두 항목이 저장되어 있다. **When** `POST /api/v1/chat`에 `{ "req_group": "REQ-001", "message": "수정 요청", ... }`을 전송한다. **Then** `state.get_sdk_session_id("REQ-001")`이 반환한 `"sess-001-abc"`가 `ClaudeAgentOptions(resume=...)` 인자로 전달되고, `state.get_sdk_session_id("REQ-002")`는 여전히 `"sess-002-xyz"`로 변경되지 않는다. | `REQ-001` 채팅 후 `sdk_sessions["REQ-001"]` 불변, `sdk_sessions["REQ-002"]` 불변. `query()` 호출 시 `resume="sess-001-abc"` 전달 확인 | 미실행 | |
| TST-009-09 | REQ-009-04 | AC-009-04 | Integration | High | **Given** `AI_BACKEND=claude_code_sdk`로 설정되어 있고, `REQ-001`과 `REQ-002` 각각에 대한 생성이 완료되어 `sdk_sessions`에 별도 session_id가 저장되어 있다. **When** `POST /api/v1/generate`에 `{ "req_group": "REQ-001", "session_id": "..." }`를 전송하여 `REQ-001`을 재생성한다. **Then** `state.get_sdk_session_id("REQ-001")`이 새 session_id로 갱신되고, `state.get_sdk_session_id("REQ-002")`는 기존 값을 유지한다. | `REQ-001` 재생성 후 `sdk_sessions["REQ-001"]` 갱신. `sdk_sessions["REQ-002"]` 기존값 유지 | 미실행 | |
| TST-SEC-27 | SEC-004-01 | REQ-004-04 | Security | High | **Given** 공격자가 채팅 입력창에 `<script>alert('XSS')</script>` 페이로드를 입력하고, `req_group`으로 `"<img onerror=alert(1) src=x>"` 형식의 XSS 페이로드를 포함한 채팅 요청을 전송한다. **When** 채팅 응답 및 채팅창 헤더의 컨텍스트 표시가 화면에 렌더링된다. **Then** React의 기본 이스케이프 처리로 스크립트가 실행되지 않고 텍스트로 표시된다. 채팅창 헤더의 `selectedReqGroup` 표시도 JSX 텍스트 표현식을 통해 이스케이프된다. | `req_group` XSS 페이로드가 이스케이프된 텍스트로 렌더링. alert 미실행. `dangerouslySetInnerHTML` 미사용 확인 | 미실행 | |
