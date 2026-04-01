# Vulcan-Claude Gate 프로세스 가이드

## 개요

Vulcan-Claude는 5-Gate 프로세스를 통해 AI 에이전트와 사람이 협업하여 프로젝트를 개발합니다.
각 Gate는 산출물 작성 → 사용자 승인 → 정합성 검증 → 상태 전환의 순서로 진행됩니다.

## Gate 흐름도

```
[Gate 1] → 승인 → [Gate 2] → 승인 → [Gate 3] → 승인 → [구현] → [Gate 4] → 승인 → [Gate 5]
 요구사항         설계            테스트계획        코딩       QA리뷰         최종승인
  @PM          @Architect       @QA        @Frontend-dev   @QA          Human
               @DBA(선택)                  @Backend-dev
```

## Gate 1: 요구사항 정의

**담당**: PM 에이전트
**산출물**: `docs/requirements/REQUIREMENTS.md`

### 수행 내용
1. 비전 질문 (배경, 대상, 가치, 성공기준)
2. 요구사항 구조화 (REQ-NNN / REQ-NNN-NN)
3. 인수 기준 작성 (AC-NNN-NN)
4. 기술 스택 협의

### 완료 조건
- 모든 REQ-NNN-NN에 AC-NNN-NN이 정의됨
- `python vulcan.py check-trace` 이슈 0건

### 전환 명령
```bash
python vulcan.py check-trace
python vulcan.py session --gate gate1 --status done --feature "기능명"
```

## Gate 2: 설계

**담당**: Architect + DBA(DB 있을 때) 에이전트
**산출물**: `docs/design/req-nnn-design.md`, `docs/design/req-nnn-data-design.md`

### 수행 내용
1. 시스템 아키텍처 설계
2. API 설계 (엔드포인트, 스키마)
3. 디렉토리 구조 정의
4. 테스트 ID 사전 할당 (TST-ID)
5. 보안 고려사항 식별 (SEC-ID)
6. 데이터 모델링 (DBA — ERD, 스키마, 마이그레이션)

### 완료 조건
- 모든 REQ 그룹에 design.md 존재
- `python vulcan.py check-trace` 이슈 0건

## Gate 3: 테스트 계획

**담당**: QA 에이전트
**산출물**: `docs/test-plan/TEST_PLAN.md`

### 수행 내용
1. 테스트 전략 수립 (Unit, Integration, E2E)
2. TST-ID ↔ REQ-ID 매핑 확인
3. 테스트 케이스 작성
4. 커버리지 목표 설정

### 완료 조건
- 모든 REQ-NNN-NN이 TEST_PLAN.md에 매핑됨
- `python vulcan.py check-trace` 이슈 0건

## 구현 (Gate 3과 Gate 4 사이)

**담당**: Frontend-dev + Backend-dev 에이전트 (REQ 그룹별 다단계 병렬 실행)

### 병렬 실행 전략

오케스트레이터가 구현 시작 시 REQ 그룹 간 의존성을 분석하여 실행 순서를 결정한다.

```
[Wave 1 - 독립적인 REQ 그룹 병렬]
  REQ-001: frontend-dev #1 || backend-dev #1
  REQ-002: frontend-dev #2 || backend-dev #2

[Wave 2 - 의존성 있는 REQ 그룹, 선행 완료 후]
  REQ-003 (REQ-001 의존): frontend-dev #3 || backend-dev #3
```

**병렬 실행 조건:**
- 동일 DB 테이블 변경이 없을 것
- REQ 그룹 간 API 호출 의존이 없을 것
- 공유 컴포넌트/모듈 충돌이 없을 것

### 수행 내용

**Frontend-dev (각 인스턴스):**
1. 프론트엔드 프로젝트 초기화, UI 컴포넌트 개발
2. 페이지/라우팅 구현, 상태관리 설정
3. API 연동 (백엔드 미완성 시 목업 데이터로 우선 개발)
4. 프론트엔드 단위 테스트 작성 (TST-ID 기반)

**Backend-dev (각 인스턴스):**
1. 백엔드 프로젝트 초기화, API 엔드포인트 구현
2. 비즈니스 로직, DB 연동, 인증/인가 구현
3. DB 마이그레이션 적용
4. 백엔드 단위 테스트 작성 (TST-ID 기반)

**공통:**
- ENVIRONMENT.md를 실제 명령어로 업데이트
- commenting-standards.md 준수
- 같은 REQ 그룹 내 Frontend-dev ↔ Backend-dev 간 API 스펙 실시간 소통

### 주의사항
- 설계 범위 밖의 판단은 하지 않는다 — 보고한다
- 설계에 없는 외부 라이브러리가 필요하면 에스컬레이션
- 병렬 인스턴스 간 파일 충돌 주의 — 공유 파일 수정 시 오케스트레이터에게 보고

## Gate 4: QA 리뷰

**담당**: QA 에이전트
**산출물**: `docs/review/req-nnn-review.md`

### 수행 내용
1. 6개 항목 평가 (A~F)
2. Blocker 항목 (A~D): 1개라도 Fail → 전체 Fail
3. Improvement 항목 (E~F): 개선 권고
4. 테스트 실행 및 결과 기록

### Blocker 항목
| 항목 | 기준 |
|------|------|
| A. 요구사항 충족 | 모든 REQ-NNN-NN 구현 여부 |
| B. 설계 준수 | 아키텍처/API 설계 준수 여부 |
| C. 테스트 결과 | 단위 테스트 전원 통과 |
| D. 보안 점검 | SEC-ID 대응 구현 여부 |

### Fail 시 재작업
1. QA가 해당 Developer(Frontend-dev/Backend-dev)에게 🔴 필수 수정 사항 전달
2. 해당 Developer 수정 후 재제출
3. QA 재검증 (최대 2회)
4. 2회 실패 시 에스컬레이션

## Gate 5: 최종 승인

**담당**: 사용자 (Human)

### 수행 내용
1. docs/review/ 의 모든 리뷰 보고서 확인
2. (선택) 코드 직접 검토
3. 최종 승인

### 전환 명령
```bash
python vulcan.py session --gate gate5 --status done --feature "기능명"
```

## 에스컬레이션

다음 상황에서는 즉시 사용자에게 보고합니다:

1. **요구사항 범위 변경** — 설계/테스트 재작업 필요
2. **QA 2회 연속 Fail** — 설계 수준 문제 가능성
3. **설계에 없는 외부 서비스/라이브러리 필요** — 아키텍처 변경
4. **Breaking 스키마 변경** — 마이그레이션 전략 승인 필요
5. **보안 취약점 발견** — 즉시 대응

## 긴급 절차 (Hotfix)

1. REQUIREMENTS.md에 최소 요구사항 작성 (1~3줄)
2. 설계 문서 생략 가능 (사용자 허용 시)
3. **Gate 4 QA 리뷰는 절대 생략 불가**
