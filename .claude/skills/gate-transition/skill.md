---
name: gate-transition
description: "Gate 전환 규칙 및 정합성 검증 스킬. 각 Gate의 완료 조건, 전환 절차, check-trace 검증 기준을 정의한다. 'Gate 완료', '다음 Gate로', 'check-trace', 'Gate 상태', '전환 조건' 등 Gate 전환 관련 요청 시 사용한다. 단, session.json 직접 수정이나 vulcan.py CLI 실행은 이 스킬의 범위가 아니다."
---

# Gate Transition — Gate 전환 규칙 및 정합성 검증

Vulcan 오케스트레이터가 Gate 전환 시 참조하는 규칙, 검증 기준, 절차를 정의한다.

## 대상 에이전트

`vulcan` 오케스트레이터 — Gate 전환 판단 시 이 스킬의 규칙을 적용한다.

## Gate 전환 조건 매트릭스

| Gate | 완료 조건 | 검증 방법 | 승인 주체 |
|------|----------|----------|----------|
| Gate 1 | 모든 REQ-NNN-NN에 AC-NNN-NN 존재 | `check-trace` (Gate 1 모드) | 사용자 |
| Gate 2 | 모든 REQ 그룹에 design.md 존재 | `check-trace` (Gate 2 모드) | 사용자 |
| Gate 3 | 모든 REQ-NNN-NN이 TEST_PLAN.md에 TST-ID 매핑 | `check-trace` (Gate 3 모드) | 사용자 |
| Gate 4 | 모든 REQ 그룹에 review.md 존재 + Blocker 전원 Pass | `check-trace` (Gate 4 모드) | 사용자 |
| Gate 5 | 사용자 최종 확인 | (수동) | 사용자 |

## Gate 전환 절차

### 표준 절차

```
1. 에이전트가 산출물 작성 완료
2. 오케스트레이터가 산출물을 사용자에게 보고
3. 사용자가 산출물 검토 및 승인
4. check-trace 실행 → 이슈 0건 확인
5. session 명령으로 Gate 상태 업데이트
6. 다음 Gate 에이전트 투입
```

### Gate 전환 실행 절차

각 Gate 완료 후 사용자 승인을 받으면 에이전트가 직접 아래를 수행한다:

**1단계 — 사용자에게 산출물 보고 (승인 요청)**
```
Gate N 산출물이 준비되었습니다.

산출물:
- [파일 목록]

승인하시면 check-trace 검증 후 Gate 상태를 자동으로 업데이트하겠습니다.
```

**2단계 — 승인 확인 후 에이전트가 직접 실행**
```bash
python vulcan.py check-trace
```
- 이슈 0건이면 계속 진행
- 이슈 있으면 사용자에게 보고 후 수정

**3단계 — check-trace 통과 시 에이전트가 직접 실행**
```bash
python vulcan.py session --gate gateN --status done --feature "기능명"
```

> **원칙**: 에이전트가 명령어를 직접 실행한다. 사용자가 터미널을 열 필요 없다.

## check-trace 검증 상세

### Gate 1 검증
- `docs/01-requirements/REQUIREMENTS.md` 파싱
- 정규식 `\bREQ-\d{3}-\d{2}\b` 로 상세 REQ-ID 추출
- 정규식 `###\s+AC-(\d{3}-\d{2})` 로 AC 정의 추출
- 각 REQ-NNN-NN에 대응하는 AC-NNN-NN 존재 여부 확인
- **누락 시**: "REQ-001-01 — AC 미정의" 이슈 보고

### Gate 2 검증
- REQ 그룹 ID(REQ-NNN) 추출
- `docs/02-design/` 디렉토리에서 `req-nnn-design.md` 파일 존재 확인
- **누락 시**: "REQ-001 — docs/02-design/req-001-design.md 없음" 이슈 보고

### Gate 3 검증
- `docs/03-test-plan/TEST_PLAN.md` 에서 REQ-NNN-NN 참조 추출
- REQUIREMENTS.md의 모든 REQ-NNN-NN이 TEST_PLAN.md에 존재하는지 확인
- **누락 시**: "REQ-001-01 — TEST_PLAN.md에 TST 매핑 없음" 이슈 보고

### Gate 4 검증
- `docs/04-review/` 디렉토리에서 `req-nnn-review.md` 파일 존재 확인
- **누락 시**: "REQ-001 — docs/04-review/req-001-review.md 없음" 이슈 보고

## 긴급 절차 (Hotfix)

긴급 버그 수정 시에도 최소한의 Gate 문서가 필요하다:

1. REQUIREMENTS.md에 1~3줄의 최소 요구사항 작성
2. 설계 문서는 생략 가능 (사용자 명시적 허용 시)
3. **Gate 4 QA 리뷰는 절대 생략 불가**
4. 사용자에게 "긴급 절차로 진행합니다. Gate 4는 반드시 수행됩니다" 안내

## session.json 상태 흐름

```
gate1:pending → gate1:done → gate2:pending → gate2:done →
gate3:pending → gate3:done → (구현) →
gate4:pending → gate4:done → gate5:pending → gate5:done → completed
```

- `done` 설정 시 `current_gate`가 자동으로 다음 Gate로 이동
- `completed` 배열에 완료 내역 추가
- Gate 5 완료 시 `current_gate`가 `"completed"`로 설정
