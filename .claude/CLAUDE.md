# REQ — Vulcan-Claude Harness

5-Gate 프로세스에 따라 에이전트 팀이 협업하여 체계적으로 개발하는 하네스.

**핵심 원칙**: 플래너는 코드를 쓰지 않는다. 실행자는 계획만 따른다.

## 구조

```
.claude/
├── agents/
│   ├── concierge.md       — 온보딩, 프로젝트 개요 파악 (프로젝트 시작 시)
│   ├── pm.md              — 요구사항 수집, REQ-ID 체계화, AC 작성 (Gate 1)
│   ├── architect.md        — 시스템 설계, API, UT-ID 사전 할당 (Gate 2)
│   ├── ui-designer.md      — UI 설계, 와이어프레임, 디자인 토큰 (Gate 2)
│   ├── dba.md              — 데이터 모델링, ERD, 마이그레이션 (Gate 2)
│   ├── frontend-dev.md     — 프론트엔드 구현, UI, 라우팅 (구현)
│   ├── backend-dev.md      — 백엔드 구현, API, DB 연동 (구현)
│   ├── ux-reviewer.md      — UI 검수, 스크린샷 분석, 접근성 (구현 후)
│   └── qa.md               — 테스트 계획 (Gate 3), 코드 리뷰 (Gate 4)
├── skills/
│   ├── vulcan/
│   │   └── skill.md         — 5-Gate 오케스트레이터 (팀 조율, 워크플로우)
│   ├── gate-transition/
│   │   └── skill.md         — Gate 전환 규칙, check-trace 검증 기준
│   └── security-baseline/
│       └── skill.md         — OWASP Top 10 체크리스트, 보안 평가 기준
└── CLAUDE.md                — 이 파일
```

## 5-Gate 프로세스

```
Gate 1        Gate 2              Gate 3        구현             UI검수        Gate 4       Gate 5
요구사항  →   설계          →   테스트계획 →   코딩        →   UX리뷰   →   QA리뷰  →  최종승인
 (PM)     (Arch+DBA+UI설계)   (QA)      (FE+BE-dev)   (UX-reviewer)   (QA)      (Human)
   ↓           ↓                 ↓          ↓              ↓            ↓          ↓
 승인→       승인→             승인→      완료→          승인→        승인→      완료
```

각 Gate는 사용자 승인 후 `check-trace` → `session` 명령으로 전환한다.

## 사용법

`/vulcan` 스킬을 트리거하거나, "Gate 1 시작해줘" 같은 자연어로 요청한다.

## Gate 산출물

| Gate | 산출물 | 경로 |
|------|--------|------|
| Gate 1 | 요구사항 정의서 | `docs/01-requirements/REQUIREMENTS.md` |
| Gate 2 | 설계 문서 | `docs/02-design/req-nnn-design.md` |
| Gate 2 | 데이터 설계 | `docs/02-design/req-nnn-data-design.md` |
| Gate 2 | UI 설계 | `docs/02-design/ui-design.md` |
| Gate 3 | 테스트 계획서 | `docs/03-test-plan/TEST_PLAN.md` |
| UI 검수 | UX 리뷰 보고서 | `docs/04-review/ux-review.md` |
| Gate 4 | QA 리뷰 보고서 | `docs/04-review/req-nnn-review.md` |

## 참조 파일

- `session.json` — Gate 진행 상태 (vulcan.py가 관리)
- `ENVIRONMENT.md` — 빌드/실행/테스트 명령어
- `commenting-standards.md` — 코드 주석 규칙
- `GATE_GUIDE.md` — Gate 프로세스 상세 가이드
- `docs/05-security/baseline.md` — 보안 기준선
