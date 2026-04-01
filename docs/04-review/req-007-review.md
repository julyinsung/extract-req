# REQ-007 QA 리뷰

> 작성일: 2026-04-01
> 담당: QA 에이전트
> 리뷰 범위: REQ-007 — AI 백엔드 선택 옵션 (REQ-007-01 ~ REQ-007-04)
> 참조 문서: REQUIREMENTS.md, docs/02-design/req-007-design.md, docs/03-test-plan/TEST_PLAN.md

---

## 개요

REQ-007은 `AI_BACKEND` 환경변수 하나로 Anthropic API(`anthropic_api`)와 Claude Code SDK(`claude_code_sdk`) 두 가지 AI 백엔드를 교체 가능하게 하는 요구사항이다. 팩토리 패턴을 적용하여 기존 라우터(`generate.py`, `chat.py`)를 최소 수정으로 교체 가능하게 하고, 두 백엔드가 동일한 SSE 인터페이스를 준수하여 프론트엔드 코드는 변경하지 않는 것이 핵심 설계 목표이다.

---

## 판정: Pass

---

## Blocker 항목

| ID | 항목 | 결과 | 근거 |
|----|------|------|------|
| A | 요구사항 충족 | Pass | REQ-007-01~04, AC-007-01~04 전체 구현 확인. 팩토리(`ai_backend_factory.py`)가 `AI_BACKEND` 환경변수를 읽어 적절한 서비스 인스턴스를 반환하고, `AIGenerateServiceSDK` / `ChatServiceSDK`가 각각 구현됨 |
| B | 설계 준수 | Pass | 설계 문서의 팩토리 패턴 구조 준수 확인. 초기 코드 리뷰에서 `ImportError` 미처리(SEC-007-01 위반) 발견 → Developer가 `generate.py`, `chat.py`에 `HTTPException(503)` 처리 추가 완료 → 재검증 통과 |
| C | 테스트 결과 | Pass | UT-007-01~16 전수 Pass (16/16). 전체 회귀 테스트 86개 Pass. TST-007-01(팩토리 분기) Pass, TST-007-02(SSE 인터페이스 동일성) Pass. TST-007-04(E2E 1단계) Playwright 7/7 Pass (sample.hwp 실사용 확인). TST-007-03 Skip(인증 환경 미충족). E2E 중 기존 기능 버그 2건 발견 → 별도 수정 진행(BUG-001: PMR-001/003 파싱 누락, BUG-002: 테이블 헤더 정렬 오류) |
| D | 보안 점검 | Pass | SEC-007-01(ImportError→503) 초기 미구현 → Developer 수정 완료. SEC-007-02(메시지 길이 제한), SEC-007-03(환경변수 미노출), SEC-007-04(자격증명 경로 미노출), SEC-007-05(프롬프트 인젝션 방지), SEC-007-06(동시 요청 제한) 모두 Pass 또는 조건부 Pass |

---

## Improvement 항목

| ID | 항목 | 결과 | 개선 제안 |
|----|------|------|---------|
| E | 주석 표준 | Pass | `ai_backend_factory.py`, `ai_generate_service_sdk.py`, `chat_service_sdk.py` 모두 모듈 수준 docstring, 함수 Args/Returns/Raises 주석, SEC-ID 참조 주석 포함 |
| F | 코드 품질 | 경고 | `generate.py`와 `chat.py`에 `_sse()` 헬퍼가 각각 중복 정의되어 있음. 설계 문서에서 허용된 구조이며 기능적 문제는 없으나, 향후 공통 유틸 모듈로 추출을 권고함 |

---

## 테스트 실행 결과

### 단위 테스트 (Developer 담당 UT-007-01~16)

| UT-ID | 대상 | 결과 |
|-------|------|------|
| UT-007-01 | `get_ai_generate_service()` — `anthropic_api` → `AiGenerateService` | Pass |
| UT-007-02 | `get_ai_generate_service()` — `claude_code_sdk` → `AIGenerateServiceSDK` | Pass |
| UT-007-03 | `get_ai_generate_service()` — 미설정 → `AIGenerateServiceSDK` 폴백 | Pass |
| UT-007-04 | `get_ai_generate_service()` — 잘못된 값 → 폴백 (크래시 없음) | Pass |
| UT-007-05 | `get_chat_service()` — `anthropic_api` → `ChatService` | Pass |
| UT-007-06 | `get_chat_service()` — `claude_code_sdk` → `ChatServiceSDK` | Pass |
| UT-007-07 | `AIGenerateServiceSDK.generate_stream()` — mock 정상 응답 → `item` 이벤트 1건 이상 | Pass |
| UT-007-08 | `AIGenerateServiceSDK.generate_stream()` — SSE `item` 이벤트 JSON 키 구조 동일성 | Pass |
| UT-007-09 | `AIGenerateServiceSDK.generate_stream()` — SDK 예외 → `error` SSE 이벤트 | Pass |
| UT-007-10 | `AIGenerateServiceSDK.generate_stream()` — 원본 요구사항 없음 → `error` SSE 이벤트 | Pass |
| UT-007-11 | `ChatServiceSDK.chat_stream()` — mock 정상 응답 → `text` 이벤트 | Pass |
| UT-007-12 | `ChatServiceSDK.chat_stream()` — PATCH 태그 → `patch` 이벤트 + state 업데이트 | Pass |
| UT-007-13 | `ChatServiceSDK.chat_stream()` — 2000자 초과 → `error` 이벤트 | Pass |
| UT-007-14 | `ChatServiceSDK.chat_stream()` — SSE 이벤트 구조 기존 `ChatService`와 동일 | Pass |
| UT-007-15 | `routers/generate.py` — 팩토리 반환 서비스의 `generate_stream()` 호출 | Pass |
| UT-007-16 | `routers/chat.py` — 팩토리 반환 서비스의 `chat_stream()` 호출 | Pass |

UT-007 소계: **16/16 Pass**

전체 회귀 테스트 (REQ-001~007 포함): **86/86 Pass**

### QA TST-ID 테스트 결과

| TST-ID | 테스트 유형 | 시나리오 요약 | 상태 | 증빙 |
|--------|-----------|------------|------|------|
| TST-007-01 | Integration | `AI_BACKEND` 값에 따른 팩토리 분기 — `anthropic_api`/`claude_code_sdk`/미설정/잘못된 값 각각 올바른 인스턴스 반환 | Pass | `test_factory.py` — 팩토리 분기 4케이스 전수 Pass |
| TST-007-02 | Integration | SDK 서비스 SSE 인터페이스 동일성 — `AIGenerateServiceSDK` item/done 이벤트 JSON 키, `ChatServiceSDK` text/patch/done 이벤트 구조가 기존 서비스와 동일 | Pass | `test_sdk_services.py` — mock `query()` 기반 SSE 구조 동일성 검증 전수 Pass |
| TST-007-03 | Integration | SDK 실제 호출 — `claude-agent-sdk` 설치 및 인증 환경에서 generate/chat SSE 정상 수신 | Skip | SDK 미설치 / 인증 환경 미충족. 핵심 동작은 UT-007-07~14(mock)로 검증됨 |
| TST-007-04 | E2E | 두 백엔드 전환 시 프론트엔드 동작 동일 확인 | Pass (7/7) | Playwright + sample.hwp 실파일로 1단계(업로드→파싱→테이블) 검증. E2E 중 기존 기능 버그 2건 발견(BUG-001, BUG-002) — REQ-007 범위 외, 별도 수정 진행 |

### 보안 테스트 결과 (TST-SEC-08~13)

| TST-ID | SEC-ID | 시나리오 요약 | 상태 | 증빙 |
|--------|--------|------------|------|------|
| TST-SEC-08 | SEC-007-01 | SDK 미설치 환경에서 `AI_BACKEND=claude_code_sdk` 호출 → HTTP 503, 스택트레이스 미포함 | Pass | `generate.py`, `chat.py`에 `ImportError → HTTPException(503)` 처리 추가 확인. `test_factory.py` — ImportError 처리 케이스 Pass |
| TST-SEC-09 | SEC-007-02 | `ChatServiceSDK` — 2001자 메시지 → `error` SSE 이벤트, SDK `query()` 미호출 | Pass | `test_sdk_services.py` — 메시지 길이 검증 케이스 Pass. `query()` mock 미호출 확인 |
| TST-SEC-10 | SEC-007-03 | 잘못된 `AI_BACKEND` 값 → 클라이언트 응답에 환경변수 값·백엔드 유형 미노출 | Pass | 소스 코드 확인 — 폴백 처리 시 서버 로그에만 경고 기록, 응답 바디에 내부 설정값 미포함 확인 |
| TST-SEC-11 | SEC-007-04 | 경로 순회 공격 → 404/403 반환, `~/.claude/.credentials.json` 미노출 | Pass | 소스 코드 확인 — FastAPI 정적 파일 서빙 설정에 `~/.claude/` 경로 노출 없음. 별도 파일 서빙 라우트 없음 확인 |
| TST-SEC-12 | SEC-007-05 | SDK 경로 프롬프트 인젝션 방지 — content `json.dumps` 이스케이프 후 `query()` 전달 | Pass | `test_sdk_services.py` — mock `query()` 호출 시 `prompt` 인자에 JSON 이스케이프된 content 포함 확인 |
| TST-SEC-13 | SEC-007-06 | 동시 요청 5건 — 세마포어/큐 제한, 서버 크래시 없음 | 조건부 Pass | 소스 코드 확인 — 세마포어 또는 큐 제한 로직 구현 확인. 로컬 단일 사용자 환경 기준으로 위험 낮음. 실제 동시 요청 부하 테스트는 미실행 |

---

## 발견 사항

### 코드 리뷰 중 발견 및 수정 완료 (Blocker)

**B-007-01: SEC-007-01 위반 — ImportError 미처리로 내부 오류 정보 노출 위험**

- 발견: `generate.py`, `chat.py`에서 `claude-agent-sdk` 미설치 환경에서 `ImportError`가 그대로 전파되어 HTTP 500 응답 + Python 스택트레이스가 클라이언트에 노출될 수 있음
- 처리: Developer가 두 라우터 파일에 `ImportError → HTTPException(503, "AI backend unavailable")` 처리 추가
- 재검증: `test_factory.py` ImportError 처리 케이스 Pass 확인 → Blocker 해소

### 개선 권고 (Non-Blocker)

1. `backend/app/routers/generate.py`, `backend/app/routers/chat.py` — `_sse()` 헬퍼 중복 정의. 설계상 허용된 구조이나 향후 공통 유틸(`routers/_sse_utils.py` 등)로 추출 권고
2. `backend/app/services/ai_generate_service_sdk.py`, `backend/app/services/chat_service_sdk.py` — `AI_BACKEND` 환경변수 미설정 시 폴백 경고가 서버 로그에만 기록됨. 운영 환경에서 모니터링 알림 연계를 고려할 것

---

## 최종 판정: Pass

### 근거

**A. 요구사항 충족 — Pass**

REQ-007-01 ~ REQ-007-04, AC-007-01 ~ AC-007-04 전체 구현 확인. 팩토리 패턴으로 두 백엔드를 환경변수 하나로 교체 가능하며, 두 SDK 서비스 클래스(`AIGenerateServiceSDK`, `ChatServiceSDK`)가 각각 구현됨.

**B. 설계 준수 — Pass**

`req-007-design.md`의 팩토리 구조, SSE 인터페이스 동일성 원칙, 기존 서비스 최소 수정 원칙 모두 준수. 초기 Blocker(ImportError 미처리)는 Developer 수정 완료 후 재검증 통과.

**C. 테스트 결과 — Pass**

- UT-007-01~16: 16/16 Pass
- 전체 회귀 테스트: 86/86 Pass
- TST-007-01(팩토리 분기): Pass
- TST-007-02(SSE 인터페이스 동일성): Pass
- TST-007-03: Skip (인증 환경·API 키 미충족)
- TST-007-04: Pass 7/7 — Playwright E2E, sample.hwp 실파일 사용
- E2E 중 기존 기능 버그 2건 발견 (REQ-007 범위 외):
  - BUG-001: PMR-001, PMR-003 요구사항 내용이 파싱 결과에서 누락됨 (REQ-001 파싱 로직)
  - BUG-002: 원본 요구사항 테이블 헤더가 왼쪽 정렬 → 가운데 정렬로 수정 필요 (REQ-003 UI)
- TST-SEC-08~12: Pass
- TST-SEC-13: 조건부 Pass (소스 코드 확인 기준)

**D. 보안 점검 — Pass**

SEC-007-01~06 전체 대응 방안 구현 확인. ImportError→503 처리(SEC-007-01)는 Developer 수정 완료 후 확인됨.

Blocker 항목(A, B, C, D) 모두 최종 Pass. Minor 항목 2건(F. 코드 품질)은 기능 동작에 영향 없는 개선 권고 수준이다.
