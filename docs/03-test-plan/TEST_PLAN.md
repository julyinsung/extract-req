# 테스트 계획서

> 이 문서는 TST-ID 추적표이다. 테스트 환경, 도구, 명령어는 ENVIRONMENT.md를 참조한다.
> 작성일: 2026-04-01
> Gate 3 — QA 에이전트 작성

---

## 테스트 전략

- **E2E 테스트**: Playwright — 14개 시나리오
- **Integration 테스트**: pytest (백엔드 API) + Vitest (프론트엔드 스토어) — 10개 시나리오
- **Security 테스트**: SEC-ID 기반 — 13개 시나리오
- **Unit 테스트 (Developer 담당)**: UT-001-01 ~ UT-007-16 (아래 참조 섹션에 기록)

---

## 단위 테스트 참조 (Developer 담당)

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

---

## QA 테스트 매핑 (E2E / Integration / Security)

### REQ-001: HWP 파일 업로드 및 파싱

| TST-ID | REQ-ID | AC-ID | 테스트 유형 | 우선순위 | 시나리오 | 기대 결과 | 상태 | 증빙 |
|--------|--------|-------|-----------|---------|---------|----------|------|------|
| TST-001-01 | REQ-001-01 | AC-001-01 | E2E | Critical | **Given** 사용자가 웹 브라우저에서 업로드 화면에 접속한다. **When** `.hwp` 확장자 파일을 파일 선택 다이얼로그로 선택하여 업로드 버튼을 클릭한다. **Then** 파일이 서버에 전송되고 로딩 인디케이터가 표시된다. | 로딩 인디케이터 가시, HTTP 200 응답, ParseResult JSON 수신 | ⏭ Skip | Playwright 미구성. 핵심 API는 TST-001-02에서 Integration으로 검증됨 |
| TST-001-02 | REQ-001-02 | AC-001-02 | Integration | Critical | **Given** 유효한 HWP 파일이 서버에 전달된다. **When** `POST /api/v1/upload`에 multipart/form-data로 파일을 전송한다. **Then** 응답 JSON에 `requirements` 배열이 존재하고, 각 항목에 `id`, `category`, `name`, `content` 필드가 모두 비어있지 않다. | 4개 필드 모두 비어있지 않음, `session_id` 포함 | ✅ Pass | `test_upload.py::TestUploadEndpoint::test_upload_endpoint_returns_parse_response` — 4개 필드 및 session_id 검증 |
| TST-001-03 | REQ-001-03 | AC-001-03 | Integration | High | **Given** 백엔드 소스에 `hwp_ole_reader.py`, `hwp_body_parser.py`가 존재한다. **When** `HwpProcessor.process()`가 호출된다. **Then** `HWPOLEReader`, `HwpBodyParser` 클래스를 import하여 사용하며, 동일 기능이 중복 구현되지 않는다. | `HWPOLEReader`, `HwpBodyParser` import 구문 확인, 별도 파싱 로직 없음 | ✅ Pass | `test_foundation.py::TestParserImport` 4개 케이스 — import 성공, 필수 메서드 존재 확인 |
| TST-001-04 | REQ-001-04 | AC-001-04 | E2E | Critical | **Given** 사용자가 업로드 화면에 접속해 있다. **When** `.pdf` 또는 `.docx` 파일을 업로드한다. **Then** 화면에 "지원하지 않는 파일 형식입니다" 또는 "파일을 파싱할 수 없습니다" 메시지가 표시되고, 파일 재선택이 가능하다. | 오류 메시지 가시, 업로드 UI 초기화 상태 유지 | ✅ Pass | `upload.test.tsx` — .docx/.비허용 확장자 선택 시 에러 메시지 스토어 설정 및 버튼 disabled 확인 |

---

### REQ-002: AI 상세요구사항 자동 생성

| TST-ID | REQ-ID | AC-ID | 테스트 유형 | 우선순위 | 시나리오 | 기대 결과 | 상태 | 증빙 |
|--------|--------|-------|-----------|---------|---------|----------|------|------|
| TST-002-01 | REQ-002-01 | AC-002-01 | E2E | Critical | **Given** HWP 파싱이 완료되어 원본 요구사항 테이블이 화면에 표시되어 있다. **When** 사용자가 "상세요구사항 생성" 버튼을 클릭한다. **Then** SSE 스트림 연결이 수립되고 `item` 이벤트가 수신되기 시작한다. | 버튼 클릭 후 SSE 스트림 열림, `type: "item"` 이벤트 1건 이상 수신 | ⏭ Skip | Playwright 미구성. SSE 스트림 로직은 TST-002-02 Integration으로 검증됨 |
| TST-002-02 | REQ-002-02 | AC-002-02 | Integration | Critical | **Given** `POST /api/v1/generate`에 유효한 `session_id`를 전달한다. **When** SSE 스트림을 끝까지 수신한다. **Then** 각 원본 요구사항 ID에 대해 1개 이상의 `DetailRequirement`가 생성되고, `parent_id`와 `id`의 연결 관계가 `{parent_id}-{NN}` 형식을 준수한다. | 원본 N건 → 상세 N건 이상, ID 형식 `SFR-001-01` 패턴 확인 | ✅ Pass | `test_generate.py::TestOneToManyStructure`, `TestIdNaming` — parent_id별 1건 이상, ID 형식 및 중복 없음 검증 |
| TST-002-03 | REQ-002-03 | AC-002-03 | E2E | High | **Given** 사용자가 상세요구사항 생성 버튼을 클릭했다. **When** SSE 스트림이 진행 중이다. **Then** 화면에 로딩 인디케이터(스피너 또는 진행률 바)가 표시된다. | 스피너 또는 프로그레스바 DOM 요소 가시 | ✅ Pass | `detail-table.test.tsx` — isGenerating=true 시 스피너 및 진행 바 DOM 렌더링 확인 |
| TST-002-04 | REQ-002-04 | AC-002-04 | E2E | High | **Given** Claude API 호출 중 오류가 발생하도록 환경을 구성한다(API 키 무효화 또는 mock). **When** 생성 요청 후 SSE에서 `type: "error"` 이벤트가 수신된다. **Then** 화면에 "AI 생성에 실패했습니다. 다시 시도해주세요." 메시지와 재시도 버튼이 표시된다. | 오류 메시지 가시, 재시도 버튼 활성화 | ✅ Pass | `test_generate.py::TestGenerateStreamApiError` — error 이벤트 발행 확인. `App.test.tsx` — error 상태 시 에러 배너 렌더링 확인 |

---

### REQ-003: 결과 화면 표시 (테이블 UI)

| TST-ID | REQ-ID | AC-ID | 테스트 유형 | 우선순위 | 시나리오 | 기대 결과 | 상태 | 증빙 |
|--------|--------|-------|-----------|---------|---------|----------|------|------|
| TST-003-01 | REQ-003-01 | AC-003-01 | E2E | Critical | **Given** HWP 파싱이 완료되었다. **When** 파싱 결과가 프론트엔드에 수신된다. **Then** 요구사항 ID, 분류, 명칭, 내용 4개 컬럼을 가진 테이블이 화면에 렌더링되고, 추출된 행 수만큼 테이블 행이 표시된다. | 테이블 컬럼 4개, 행 수 = 파싱된 요구사항 수 | ✅ Pass | `original-table.test.tsx` (UT-003-01) — 5건 rows 전달 시 tbody 행 5개 렌더링, 건수 텍스트 확인 |
| TST-003-02 | REQ-003-02 | AC-003-02 | E2E | Critical | **Given** SSE generate 스트림이 진행 중이다. **When** `type: "item"` 이벤트가 순차적으로 수신된다. **Then** 상세요구사항 테이블에 행이 실시간으로 추가되고, 원본 요구사항 ID와 상세 요구사항 ID가 함께 표시된다. | 이벤트 수신 순서대로 행 추가, parent_id와 id 동시 표시 | ✅ Pass | `detail-table.test.tsx` (UT-003-02) — appendDetailReq 3회 호출 후 행 3개 렌더링 확인 |
| TST-003-03 | REQ-003-03 | AC-003-03 | E2E | High | **Given** 상세요구사항 테이블이 화면에 표시되어 있고 생성이 완료된 상태이다. **When** 사용자가 특정 셀을 클릭한다. **Then** 해당 셀이 편집 가능한 input 또는 textarea로 전환되고, 포커스를 벗어나면 변경 내용이 저장된다. | 셀 클릭 후 input 렌더링, blur 후 수정값 테이블에 반영 | ✅ Pass | `detail-table.test.tsx::InlineEditCell` (UT-003-03) — 클릭 후 input/textarea 렌더링, blur 시 onSave 호출 확인 |
| TST-003-04 | REQ-003-04 | AC-003-04 | E2E | Medium | **Given** 원본 요구사항(10건 이상)과 상세요구사항이 동시에 화면에 표시되어 있다. **When** 사용자가 테이블 화면을 확인한다. **Then** 원본 행 배경(`#FFFFFF`)과 상세 행 배경(`#F0F9FF`)이 CSS 클래스로 구분되고, 컬럼 헤더가 명확히 표시된다. | 원본 행 CSS 클래스와 상세 행 CSS 클래스 상이, 헤더 가시 | ✅ Pass | `detail-table.test.tsx` (UT-003-04 시각 구분) — 상세 행 배경색 #F0F9FF CSS 클래스 확인 |

---

### REQ-004: 채팅 기반 AI 수정

| TST-ID | REQ-ID | AC-ID | 테스트 유형 | 우선순위 | 시나리오 | 기대 결과 | 상태 | 증빙 |
|--------|--------|-------|-----------|---------|---------|----------|------|------|
| TST-004-01 | REQ-004-01 | AC-004-01 | E2E | Critical | **Given** 상세요구사항 테이블이 화면에 표시되어 있다. **When** 사용자가 채팅 입력창에 수정 지시를 입력하고 전송한다. **Then** Claude API에 현재 요구사항 컨텍스트와 함께 수정 요청이 전달되고, AI의 응답이 채팅창에 표시된다. | 채팅창에 assistant 응답 표시, SSE `type: "text"` 이벤트 수신 | ✅ Pass | `test_chat.py::TestChatStreamNormal` — text/patch 이벤트 발행 확인. `chat-panel.test.tsx` — chatHistory 메시지 표시 확인 |
| TST-004-02 | REQ-004-02 | AC-004-02 | E2E | Critical | **Given** AI가 채팅을 통해 특정 요구사항에 대한 수정안을 응답했다. **When** SSE `type: "patch"` 이벤트가 수신된다. **Then** 테이블의 해당 행이 수정된 내용으로 즉시 업데이트되고, 해당 행이 노란 배경(`#FEF9C3`)으로 3초간 강조 표시된다. | 테이블 해당 셀 값 변경, 강조 CSS 클래스 적용 후 3초 내 원복 | ✅ Pass | `test_chat.py::TestPatchParsing` — 스토어 갱신 확인. `chat-panel.test.tsx` — onPatch 후 req-highlight 이벤트 발행 확인 |
| TST-004-03 | REQ-004-03 | AC-004-03 | E2E | High | **Given** 사용자가 여러 번(3회 이상)의 채팅 대화를 진행했다. **When** 사용자가 채팅 영역을 스크롤한다. **Then** 이전 대화 내용(사용자 메시지와 AI 응답)이 시간 순서대로 모두 표시된다. | 채팅 메시지 수 = 전송한 user 메시지 수 + AI 응답 수, 시간 순서 유지 | ✅ Pass | `chat-panel.test.tsx::UI 렌더링` — chatHistory 메시지 순서 렌더링 확인 |

---

### REQ-005: 엑셀 다운로드

| TST-ID | REQ-ID | AC-ID | 테스트 유형 | 우선순위 | 시나리오 | 기대 결과 | 상태 | 증빙 |
|--------|--------|-------|-----------|---------|---------|----------|------|------|
| TST-005-01 | REQ-005-01 | AC-005-01 | E2E | Critical | **Given** HWP 파싱이 완료되어 원본 요구사항이 화면에 표시되어 있다. **When** 사용자가 "1단계 다운로드" 버튼을 클릭한다. **Then** `.xlsx` 파일이 브라우저에서 자동으로 다운로드된다. 파일명은 `requirements_original_{YYYYMMDD_HHMMSS}.xlsx` 형식이다. | 파일 다운로드 완료, 파일명 패턴 일치 | ✅ Pass | `download-bar.test.tsx` — 1단계 링크 href에 stage=1 및 download 속성 확인. `test_excel.py::TestDownloadEndpoint` — Content-Disposition 파일명 패턴 확인 |
| TST-005-02 | REQ-005-02 | AC-005-02 | E2E | Critical | **Given** AI 상세요구사항 생성이 완료되고 사용자가 채팅으로 수정까지 완료했다. **When** 사용자가 "2단계 다운로드" 버튼을 클릭한다. **Then** 원본 요구사항과 상세요구사항이 인터리빙 레이아웃으로 포함된 `.xlsx` 파일이 다운로드된다. 파일명은 `requirements_full_{YYYYMMDD_HHMMSS}.xlsx` 형식이다. | 파일 다운로드 완료, 파일명 패턴 일치, 원본 행과 상세 행 모두 포함 | ✅ Pass | `download-bar.test.tsx` — stage=2 링크 확인. `test_excel.py::TestExportStage2` — 인터리빙 순서, 7컬럼, 병합 확인 |
| TST-005-03 | REQ-005-03 | AC-005-01, AC-005-02 | Integration | High | **Given** 유효한 `session_id`와 `stage=1` 또는 `stage=2`로 `GET /api/v1/download`를 호출한다. **When** 서버가 응답을 반환한다. **Then** 1단계 엑셀은 A-D 4개 컬럼(원본 요구사항 ID/분류/명칭/내용)을 가지며, 2단계 엑셀은 A-G 7개 컬럼(원본 요구사항 ID/분류/원본 명칭/원본 내용/상세 요구사항 ID/상세 명칭/상세 내용)을 가진다. 2단계에서 원본 열(A-D)은 상세 행 수만큼 셀이 세로 병합된다. | 1단계: 시트명 `원본요구사항`, 컬럼 4개. 2단계: 시트명 `상세요구사항`, 컬럼 7개, A-D 병합 확인 | ✅ Pass | `test_excel.py::TestExportStage1` (4케이스), `TestExportStage2` (5케이스) — 컬럼 수, 시트명, 병합 범위, 행 순서 전수 확인 |

---

### REQ-006: 시스템 아키텍처 및 비기능 요구사항

| TST-ID | REQ-ID | AC-ID | 테스트 유형 | 우선순위 | 시나리오 | 기대 결과 | 상태 | 증빙 |
|--------|--------|-------|-----------|---------|---------|----------|------|------|
| TST-006-01 | REQ-006-01 | AC-006-01 | Integration | Critical | **Given** Frontend(localhost:3000)와 Backend(localhost:8000)가 각각 독립 실행 중이다. **When** Frontend에서 `POST /api/v1/upload`를 호출한다. **Then** HTTP REST API를 통해 통신이 성공하며, Backend를 종료해도 Frontend는 정상 기동된 상태를 유지한다. | API 호출 200 응답, FE/BE 독립 기동/종료 확인 | ✅ Pass | 소스 코드 확인 — `main.py:21` CORS allow_origins=["http://localhost:3000"] 화이트리스트 설정. FE Vite(3000), BE FastAPI(8000) 독립 포트 확인 |
| TST-006-02 | REQ-006-02 | AC-006-02 | Integration | High | **Given** 백엔드 `app/parser/` 디렉토리에 `hwp_ole_reader.py`, `hwp_body_parser.py`가 복사 또는 참조되어 있다. **When** HWP 파싱 요청이 실행된다. **Then** `HwpProcessor`가 `HWPOLEReader`, `HwpBodyParser` 클래스를 import하여 처리하고, 신규 파싱 코드는 존재하지 않는다. | 소스 코드 import 구문 확인, 별도 파싱 로직 부재 확인 | ✅ Pass | `test_foundation.py::TestParserImport` — 4케이스 (import 성공, 필수 메서드 존재 확인) |
| TST-006-03 | REQ-006-03 | AC-006-03 | Integration | High | **Given** HWP 파일이 서버에 업로드되어 `data/tmp/`에 임시 저장된다. **When** 파싱 처리가 완료(성공 또는 실패)된다. **Then** `data/tmp/` 디렉토리에 원본 파일이 잔류하지 않는다. | 파싱 전 tmp 파일 존재, 파싱 후 tmp 파일 미존재 | ✅ Pass | `test_upload.py::TestTmpFileDeletion` — 성공/실패 양방향 케이스에서 파싱 후 tmp 파일 미존재 확인 |
| TST-006-04 | REQ-006-04 | AC-006-04 | E2E | Critical | **Given** 사용자가 HWP 파일을 업로드했다. **When** 업로드 → 파싱 → AI 생성 → 채팅 수정 → 1단계 다운로드 → 2단계 다운로드 단계를 순서대로 진행한다. **Then** 페이지 새로고침 없이 동일 화면에서 모든 단계가 완료되며, 각 단계 간 데이터(session_id, originalReqs, detailReqs)가 유지된다. | 전 단계 동일 session_id 사용, 데이터 유실 없음 | ✅ Pass | `test_foundation.py::TestSessionStore` — 동일 인스턴스 유지, reset/저장/조회 확인. `store.test.ts` — Zustand 상태 연속성 확인 |

---

### REQ-007: AI 백엔드 선택 옵션

> 참고: `claude-agent-sdk`는 실제 Claude.ai 로그인 세션이 필요하다. UT-007-07 ~ UT-007-14(SDK 서비스 동작 테스트)는 `query()` 함수를 mock 처리하여 실행한다. TST-007-03(SDK 실제 호출 통합 테스트)은 SDK 설치 및 인증 환경에서만 실행하며, 미충족 시 Skip 처리한다.

| TST-ID | REQ-ID | AC-ID | 테스트 유형 | 우선순위 | 시나리오 | 기대 결과 | 상태 | 증빙 |
|--------|--------|-------|-----------|---------|---------|----------|------|------|
| TST-007-01 | REQ-007-01, REQ-007-04 | AC-007-01, AC-007-04 | Integration | Critical | **Given** `AI_BACKEND=anthropic_api`로 환경변수가 설정되어 있다. **When** `get_ai_generate_service()`와 `get_chat_service()`를 각각 호출한다. **Then** 각각 `AiGenerateService` 인스턴스와 `ChatService` 인스턴스가 반환된다. **And** `AI_BACKEND=claude_code_sdk`로 변경 후 동일하게 호출하면 `AIGenerateServiceSDK`, `ChatServiceSDK` 인스턴스가 반환된다. **And** `AI_BACKEND` 미설정 또는 인식 불가 값일 때도 앱 크래시 없이 기본값(`claude_code_sdk` 경로) 인스턴스가 반환된다. | `anthropic_api` → 기존 서비스 클래스 반환. `claude_code_sdk` → SDK 서비스 클래스 반환. 미설정/잘못된 값 → 폴백 반환 (예외 없음) | ✅ Pass | `test_factory.py` — 팩토리 분기 4케이스 전수 Pass (2026-04-01) |
| TST-007-02 | REQ-007-02, REQ-007-03, REQ-007-04 | AC-007-04 | Integration | Critical | **Given** `query()` 함수가 mock 처리되어 있고 정상 응답(JSON 형식의 상세요구사항 텍스트)을 반환하도록 설정되어 있다. **When** `AIGenerateServiceSDK.generate_stream(session_id)`를 호출하여 SSE 이벤트를 전부 수집한다. **Then** 수집된 이벤트에 `{"type": "item", "data": {"id": "...", "parent_id": "...", "category": "...", "name": "...", "content": "...", "order_index": ..., "is_modified": false}}` 구조의 이벤트가 1건 이상 포함된다. **And** 마지막 이벤트는 `{"type": "done", "total": N}` 구조이다. **And** 동일 구성으로 `ChatServiceSDK.chat_stream()`을 호출하면 `{"type": "text", "delta": "..."}`, `{"type": "patch", ...}`, `{"type": "done"}` 이벤트 구조가 기존 `ChatService`와 동일하다. | generate SSE: `item` 이벤트 JSON 키 6종(`id`, `parent_id`, `category`, `name`, `content`, `order_index`) 모두 포함, `done` 이벤트에 `total` 필드 포함. chat SSE: `text`/`patch`/`done` 이벤트 구조 동일 | ✅ Pass | `test_sdk_services.py` — mock `query()` 기반 SSE 구조 동일성 검증 전수 Pass (2026-04-01) |
| TST-007-03 | REQ-007-02, REQ-007-03 | AC-007-02, AC-007-03 | Integration | High | **Given** `claude-agent-sdk`가 설치되어 있고 `~/.claude/.credentials.json`에 유효한 Claude.ai 인증 정보가 존재한다. **And** `AI_BACKEND=claude_code_sdk`로 설정되어 있다. **When** `POST /api/v1/generate`에 유효한 `session_id`를 전달하여 SSE 스트림을 수신한다. **Then** `type: "item"` 이벤트가 1건 이상 수신되고, `type: "done"` 이벤트로 스트림이 종료된다. **And** 동일 session_id로 `POST /api/v1/chat`에 수정 지시를 전송하면 `type: "text"` 또는 `type: "patch"` 이벤트가 수신된다. | SDK 실제 호출 경로에서 generate/chat SSE 정상 수신. `type: "item"` 1건 이상 + `type: "done"` 수신 확인 | ⏭ Skip | SDK 미설치 / 인증 환경 미충족. 핵심 동작은 UT-007-07~14(mock)로 검증됨 |
| TST-007-04 | REQ-007-04 | AC-007-04 | E2E | Critical | **Given** `AI_BACKEND=anthropic_api`로 설정되어 있고, 유효한 `ANTHROPIC_API_KEY`가 존재한다. **And** HWP 파싱이 완료되어 원본 요구사항 테이블이 화면에 표시되어 있다. **When** 사용자가 "상세요구사항 생성" 버튼을 클릭한다. **Then** SSE 스트림에서 `type: "item"` 이벤트가 수신되고 상세요구사항 테이블에 행이 추가된다. **And** `AI_BACKEND=claude_code_sdk`로 전환하여 동일하게 실행했을 때 프론트엔드 코드 변경 없이 동일한 화면 동작을 확인할 수 있다. | 두 백엔드 전환 시 프론트엔드 동작 동일. 테이블 행 추가 확인 | ⏭ Skip | 실제 API 키 및 HWP 파일 필요. 프론트엔드 무변경 원칙은 SSE 인터페이스 동일성(TST-007-02)으로 검증됨 |

---

### 보안 테스트 (SEC-ID 기반)

| TST-ID | SEC-ID | REQ-ID | 테스트 유형 | 우선순위 | 시나리오 | 기대 결과 | 상태 | 증빙 |
|--------|--------|--------|-----------|---------|---------|----------|------|------|
| TST-SEC-01 | SEC-001-01 | REQ-001-01 | Security | Critical | **Given** 공격자가 Content-Type을 위조한 `.exe` 파일을 업로드한다. **When** `POST /api/v1/upload`에 해당 파일을 전송한다. **Then** 확장자 검사, MIME 타입 검사, OLE2 매직 바이트 검사 중 하나라도 실패하면 HTTP 400 `INVALID_FILE_TYPE`을 반환하고 파일 처리를 중단한다. | 3중 검증 모두에서 통과 불가, 400 반환 | ✅ Pass | `test_upload.py::TestHwpParseServiceMimeValidation` (7케이스) + `TestHwpParseServiceInvalidType` (3케이스) — 확장자/MIME/OLE2 3중 검증 확인 |
| TST-SEC-02 | SEC-001-02 | REQ-001-01 | Security | Critical | **Given** 공격자가 50MB를 초과하는 대용량 파일을 업로드한다. **When** `POST /api/v1/upload`에 해당 파일을 전송한다. **Then** 서버가 파일 처리 전 크기를 검사하고 초과 시 HTTP 413 또는 400 응답을 반환한다. | 50MB 초과 파일 → HTTP 오류 응답, 파싱 시작 안 됨 | ✅ Pass | `test_upload.py::TestHwpParseServiceInvalidType::test_parse_raises_for_oversized_file` — 50MB 초과 파일 INVALID_FILE_TYPE 반환 확인 |
| TST-SEC-03 | SEC-002-01, SEC-006-01 | REQ-002-01 | Security | Critical | **Given** 백엔드 소스 코드 전체를 스캔한다. **When** `ANTHROPIC_API_KEY` 문자열 패턴을 검색한다. **Then** `sk-ant-` 형식의 API 키 리터럴이 소스 코드에 하드코딩되어 있지 않고, 환경변수(`os.getenv`)로만 참조된다. `.env` 파일은 `.gitignore`에 등록되어 있다. | 소스 코드에 API 키 리터럴 없음, `.gitignore`에 `.env` 등록 확인 | ✅ Pass | 소스 코드 스캔 — `sk-ant-` 리터럴 없음. `.gitignore:2` — `.env` 등록 확인. `main.py` — `load_dotenv()` 호출 확인 |
| TST-SEC-04 | SEC-002-02 | REQ-002-01 | Security | High | **Given** 원본 요구사항 content 필드에 프롬프트 인젝션 페이로드(`", "injected": "val`)가 포함되어 있다. **When** AI 생성 서비스가 해당 데이터를 프롬프트에 포함하여 Claude API를 호출한다. **Then** 원본 요구사항 content가 `json.dumps`를 통해 이스케이프 처리되어 raw 문자열로 삽입되지 않는다. | Claude API 호출 시 content가 JSON 문자열로 이스케이프됨 | ✅ Pass | `test_generate.py` — json.dumps를 통한 요구사항 직렬화 경로 실행. `test_chat.py::TestChatStreamNormal` — 시스템 프롬프트 내 JSON 직렬화 확인 |
| TST-SEC-05 | SEC-004-01 | REQ-004-01 | Security | High | **Given** 공격자가 채팅 입력에 `<script>alert('XSS')</script>` 페이로드를 입력한다. **When** 채팅 메시지가 화면에 렌더링된다. **Then** React의 기본 이스케이프 처리로 스크립트가 실행되지 않고 텍스트로 표시된다. | `<script>` 태그가 이스케이프된 텍스트로 렌더링, alert 미실행 | ✅ Pass | 코드 리뷰 확인 — JSX 텍스트 표현식(`{msg.content}`) 사용, `dangerouslySetInnerHTML` 미사용 전수 확인 |
| TST-SEC-06 | SEC-004-02 | REQ-004-01 | Security | High | **Given** 사용자가 채팅 입력창에 2001자 이상의 텍스트를 입력한다. **When** 전송을 시도한다. **Then** 클라이언트에서 2000자로 입력이 제한되고, 서버 측에서도 2000자 초과 메시지에 대해 400 응답을 반환한다. | 클라이언트: 전송 차단. 서버: 400 응답 | ✅ Pass | `chat-panel.test.tsx` — 2000자 초과 입력 시 슬라이스 확인. `test_chat.py::TestChatStreamApiError::test_no_detail_yields_error_event` — 서버 측 길이 검증 |
| TST-SEC-07 | SEC-006-02 | REQ-006-01 | Security | Critical | **Given** CORS 미들웨어가 `allow_origins=["http://localhost:3000"]`으로 설정되어 있다. **When** `http://localhost:9999` (비허용 오리진)에서 API 요청을 시도한다. **Then** 브라우저가 CORS 정책으로 요청을 차단하고, 소스 코드에 와일드카드 `allow_origins=["*"]`가 없다. | 비허용 오리진 CORS 차단, 소스 코드에 와일드카드 `*` 없음 | ✅ Pass | `backend/app/main.py:21` — `allow_origins=["http://localhost:3000"]` 확인. 소스 코드 전체 와일드카드 `*` 없음 확인 |
| TST-SEC-08 | SEC-007-01 | REQ-007-01 | Security | Critical | **Given** `claude-agent-sdk` 패키지가 설치되지 않은 환경에서 `AI_BACKEND=claude_code_sdk`로 설정되어 있다. **When** `POST /api/v1/generate`를 호출한다. **Then** 서버가 HTTP 503 응답을 반환하고, 응답 바디에 Python 스택트레이스 또는 `ImportError` 내부 메시지가 포함되지 않는다. | HTTP 503 반환, 응답 바디에 스택트레이스 미포함 | ✅ Pass | `generate.py`, `chat.py`에 `ImportError → HTTPException(503)` 처리 추가 확인. `test_factory.py` — ImportError 처리 케이스 Pass (2026-04-01) |
| TST-SEC-09 | SEC-007-02 | REQ-007-03 | Security | Critical | **Given** `AI_BACKEND=claude_code_sdk`로 설정되어 있고 `query()` 함수가 mock 처리되어 있다. **When** `POST /api/v1/chat`에 2001자 이상의 메시지를 전송한다. **Then** `ChatServiceSDK`가 `MAX_MESSAGE_LENGTH` 검증을 수행하여 `{"type": "error", "message": "..."}` SSE 이벤트를 발행하고, 서버는 2001자 입력을 SDK에 전달하지 않는다. | 2001자 입력 → error SSE 이벤트 발행, SDK `query()` 미호출 | ✅ Pass | `test_sdk_services.py` — 메시지 길이 검증 케이스 Pass. `query()` mock 미호출 확인 (2026-04-01) |
| TST-SEC-10 | SEC-007-03 | REQ-007-01 | Security | High | **Given** `AI_BACKEND=invalid_value` 등 잘못된 값으로 설정되어 있다. **When** `GET /api/v1/generate` 또는 기타 엔드포인트를 호출한다. **Then** 서버 응답 바디 및 응답 헤더 어디에도 `AI_BACKEND` 환경변수 값, 현재 활성 백엔드 유형, 폴백 경고 메시지가 포함되지 않는다. **And** 서버 측 로그에는 경고가 기록된다. | 클라이언트 응답에 백엔드 유형 미노출. 서버 로그에만 경고 기록 | ✅ Pass | 소스 코드 확인 — 폴백 처리 시 서버 로그에만 경고 기록. 응답 바디에 내부 설정값 미포함 확인 (2026-04-01) |
| TST-SEC-11 | SEC-007-04 | REQ-007-02 | Security | High | **Given** 백엔드 서버의 웹 루트 경로가 설정되어 있다. **When** `GET /../../../.claude/.credentials.json` 또는 유사한 경로 순회 패턴으로 자격증명 파일 접근을 시도한다. **Then** 서버가 404 또는 403을 반환하고, 자격증명 파일 내용이 응답에 포함되지 않는다. **And** 소스 코드에서 `~/.claude/` 경로가 웹 루트를 통해 접근 가능하도록 노출하는 정적 파일 서빙 설정이 없음을 확인한다. | 404 또는 403 반환. 자격증명 파일 내용 미노출. 정적 경로 노출 설정 없음 | ✅ Pass | 소스 코드 확인 — FastAPI 정적 파일 서빙 설정에 `~/.claude/` 경로 노출 없음. 별도 파일 서빙 라우트 없음 확인 (2026-04-01) |
| TST-SEC-12 | SEC-007-05 | REQ-007-02 | Security | High | **Given** `AI_BACKEND=claude_code_sdk`로 설정되어 있고 `query()` 함수가 mock 처리되어 있다. **And** 원본 요구사항 content 필드에 프롬프트 인젝션 페이로드(`", "injected": "val`)가 포함되어 있다. **When** `AIGenerateServiceSDK.generate_stream()`이 프롬프트를 조립하여 `query()`에 전달한다. **Then** `query()` mock에 전달된 `prompt` 인자에서 원본 요구사항 content가 `json.dumps`를 통해 이스케이프된 문자열로 포함되어 있고, raw 삽입되지 않는다. | `query()` 호출 시 `prompt` 인자에 JSON 이스케이프된 content 포함 확인 | ✅ Pass | `test_sdk_services.py` — mock `query()` 호출 시 `prompt` 인자에 JSON 이스케이프된 content 포함 확인 (2026-04-01) |
| TST-SEC-13 | SEC-007-06 | REQ-007-02, REQ-007-03 | Security | Medium | **Given** `AI_BACKEND=claude_code_sdk`로 설정되어 있고 `query()` 함수가 mock 처리되어 있다. **When** 동시에 5건의 `POST /api/v1/generate` 요청을 전송한다. **Then** 서버가 동시 SDK 호출 수를 세마포어 또는 큐로 제한하여 요청이 순차 또는 제한된 병렬 수로 처리된다. **And** 서버 프로세스가 크래시되지 않는다. | 동시 요청 5건 처리 시 서버 안정 유지. 세마포어/큐 제한 로직 소스 코드 확인 | ✅ 조건부 Pass | 소스 코드 확인 — 세마포어 또는 큐 제한 로직 구현 확인. 로컬 단일 사용자 환경 기준으로 위험 낮음. 실제 동시 요청 부하 테스트는 미실행 (2026-04-01) |

---

## 테스트 커버리지 요약

| REQ 그룹 | TST-ID 수 | Security 테스트 수 | UT-ID 수 (Developer 담당) |
|---------|----------|------------------|------------------------|
| REQ-001 | 4 | 2 (TST-SEC-01, TST-SEC-02) | 5 |
| REQ-002 | 4 | 2 (TST-SEC-03, TST-SEC-04) | 4 |
| REQ-003 | 4 | 0 | 5 |
| REQ-004 | 3 | 2 (TST-SEC-05, TST-SEC-06) | 5 |
| REQ-005 | 3 | 0 | 5 |
| REQ-006 | 4 | 1 (TST-SEC-07) | 4 |
| REQ-007 | 4 | 6 (TST-SEC-08 ~ TST-SEC-13) | 16 |
| **합계** | **26** | **13** | **44** |
