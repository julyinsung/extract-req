# 테스트 계획서

> 이 문서는 TST-ID 추적 인덱스이다. 테스트 환경, 도구, 명령어는 ENVIRONMENT.md를 참조한다.
> 작성일: 2026-04-01
> Gate 3 — QA 에이전트 작성

---

## 테스트 전략

- **E2E 테스트**: Playwright — 29개 시나리오
- **Integration 테스트**: pytest (백엔드 API) + Vitest (프론트엔드 스토어) — 28개 시나리오
- **Security 테스트**: SEC-ID 기반 — 27개 시나리오
- **Unit 테스트 (Developer 담당)**: UT-001-01 ~ UT-013-14 (아래 참조 파일에 기록)

---

## 파일 목록

| 파일 | 내용 |
|------|------|
| [ut-reference.md](ut-reference.md) | 단위 테스트 참조 (UT-ID) — UT-001-xx ~ UT-013-xx 전체 테이블 |
| [tst-001-007.md](tst-001-007.md) | QA 테스트 케이스 — REQ-001~007 (E2E / Integration / Security TST-001~SEC-13) |
| [tst-008-009.md](tst-008-009.md) | QA 테스트 케이스 — REQ-008~009 (E2E / Integration / Security TST-008~SEC-19) |
| [tst-010-013.md](tst-010-013.md) | QA 테스트 케이스 — REQ-010~013 (E2E / Integration / Security TST-010~SEC-26) |
| [tst-004-009-delta.md](tst-004-009-delta.md) | QA 테스트 케이스 — REQ-004-04/05/06, REQ-009-04 추가분 (TST-004-04~TST-009-09, TST-SEC-27) |

---

## 단위 테스트 참조 (Developer 담당)

> 상세 테이블은 [ut-reference.md](ut-reference.md)를 참조한다.
> UT-ID는 설계 문서에서 사전 할당. Developer가 구현 시 작성·실행하며, QA는 Gate 4에서 전수 Pass 여부만 확인한다.

| 범위 | UT-ID | 상태 |
|------|-------|------|
| REQ-001 | UT-001-01 ~ UT-001-05 | PASS (2026-04-01) |
| REQ-002 | UT-002-01 ~ UT-002-04 | PASS (2026-04-01) |
| REQ-003 | UT-003-01 ~ UT-003-05 | PASS (2026-04-01) |
| REQ-004 | UT-004-01 ~ UT-004-05 | PASS (2026-04-01) |
| REQ-005 | UT-005-01 ~ UT-005-05 | PASS (2026-04-01) |
| REQ-006 | UT-006-01 ~ UT-006-04 | PASS (2026-04-01) |
| REQ-007 | UT-007-01 ~ UT-007-16 | PASS (2026-04-01) |
| REQ-008 | UT-008-01 ~ UT-008-09 | PASS (2026-04-02) |
| REQ-009 | UT-009-01 ~ UT-009-07 | PASS (2026-04-02) |
| REQ-010 | UT-010-01 ~ UT-010-05 | pending |
| REQ-011 | UT-011-01 ~ UT-011-02 | pending |
| REQ-012 | UT-012-01 ~ UT-012-09 | pending |
| REQ-013 | UT-013-01 ~ UT-013-14 | pending |

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
| REQ-008 | 6 | 3 (TST-SEC-14, TST-SEC-15, TST-SEC-19) | 9 |
| REQ-009 | 9 | 3 (TST-SEC-16, TST-SEC-17, TST-SEC-18) | 7 |
| REQ-010 | 4 | 0 | 5 |
| REQ-011 | 3 | 0 | 2 |
| REQ-012 | 4 | 3 (TST-SEC-20, TST-SEC-21, TST-SEC-22) | 9 |
| REQ-013 | 8 | 4 (TST-SEC-23, TST-SEC-24, TST-SEC-25, TST-SEC-26) | 14 |
| REQ-004 (delta) | 6 | 1 (TST-SEC-27) | — |
| **합계** | **73** | **27** | **97** |

---

## TST-ID 전체 매핑 (check-trace용 인덱스)

> 상세 시나리오는 각 파일([tst-001-007.md](tst-001-007.md), [tst-008-009.md](tst-008-009.md))을 참조한다.

| TST-ID | REQ-ID | AC-ID | 테스트 유형 | 우선순위 | 상태 |
|--------|--------|-------|-----------|---------|------|
| TST-001-01 | REQ-001-01 | AC-001-01 | E2E | Critical | Pass |
| TST-001-02 | REQ-001-02 | AC-001-02 | Integration | Critical | Pass |
| TST-001-03 | REQ-001-03 | AC-001-03 | Integration | High | Pass |
| TST-001-04 | REQ-001-04 | AC-001-04 | E2E | Critical | Pass |
| TST-002-01 | REQ-002-01 | AC-002-01 | E2E | Critical | Pass |
| TST-002-02 | REQ-002-02 | AC-002-02 | Integration | Critical | Pass |
| TST-002-03 | REQ-002-03 | AC-002-03 | E2E | High | Pass |
| TST-002-04 | REQ-002-04 | AC-002-04 | E2E | High | Pass |
| TST-003-01 | REQ-003-01 | AC-003-01 | E2E | Critical | Pass |
| TST-003-02 | REQ-003-02 | AC-003-02 | E2E | Critical | Pass |
| TST-003-03 | REQ-003-03 | AC-003-03 | E2E | High | Pass |
| TST-003-04 | REQ-003-04 | AC-003-04 | E2E | Medium | Pass |
| TST-004-01 | REQ-004-01 | AC-004-01 | E2E | Critical | Pass |
| TST-004-02 | REQ-004-02 | AC-004-02 | E2E | Critical | Pass |
| TST-004-03 | REQ-004-03 | AC-004-03 | E2E | High | Pass |
| TST-005-01 | REQ-005-01 | AC-005-01 | E2E | Critical | Pass |
| TST-005-02 | REQ-005-02 | AC-005-02 | E2E | Critical | Pass |
| TST-005-03 | REQ-005-03 | AC-005-01 | Integration | High | Pass |
| TST-006-01 | REQ-006-01 | AC-006-01 | Integration | Critical | Pass |
| TST-006-02 | REQ-006-02 | AC-006-02 | Integration | High | Pass |
| TST-006-03 | REQ-006-03 | AC-006-03 | Integration | High | Pass |
| TST-006-04 | REQ-006-04 | AC-006-04 | E2E | Critical | Pass |
| TST-007-01 | REQ-007-01 | AC-007-01 | Integration | Critical | Pass |
| TST-007-02 | REQ-007-02 | AC-007-04 | Integration | Critical | Pass |
| TST-007-03 | REQ-007-03 | AC-007-02 | Integration | High | Skip |
| TST-007-04 | REQ-007-04 | AC-007-04 | E2E | Critical | Pass |
| TST-008-01 | REQ-008-01 | AC-008-01 | Integration | Critical | Pass |
| TST-008-02 | REQ-008-01 | AC-008-01 | Integration | Critical | Pass |
| TST-008-03 | REQ-008-01 | AC-008-01 | Integration | High | Pass |
| TST-008-04 | REQ-008-02 | AC-008-02 | E2E | Critical | Pass |
| TST-008-05 | REQ-008-02 | AC-008-02 | Integration | High | Pass |
| TST-008-06 | REQ-008-03 | AC-008-03 | Integration | Critical | Pass |
| TST-009-01 | REQ-009-01 | AC-009-01 | Integration | Critical | Pass |
| TST-009-02 | REQ-009-01 | AC-009-01 | Integration | High | Pass |
| TST-009-03 | REQ-009-02 | AC-009-02 | Integration | Critical | Pass |
| TST-009-04 | REQ-009-02 | AC-009-02 | Integration | High | Pass |
| TST-009-05 | REQ-009-03 | AC-009-03 | Integration | Critical | Pass |
| TST-009-06 | REQ-009-03 | AC-009-03 | Integration | High | Pass |
| TST-009-07 | REQ-009-01 | AC-009-01 | E2E | High | Pass |
| TST-SEC-01 | REQ-001-01 | SEC-001-01 | Security | Critical | Pass |
| TST-SEC-02 | REQ-001-01 | SEC-001-02 | Security | Critical | Pass |
| TST-SEC-03 | REQ-002-01 | SEC-002-01 | Security | Critical | Pass |
| TST-SEC-04 | REQ-002-01 | SEC-002-02 | Security | High | Pass |
| TST-SEC-05 | REQ-004-01 | SEC-004-01 | Security | High | Pass |
| TST-SEC-06 | REQ-004-01 | SEC-004-02 | Security | High | Pass |
| TST-SEC-07 | REQ-006-01 | SEC-006-02 | Security | Critical | Pass |
| TST-SEC-08 | REQ-007-01 | SEC-007-01 | Security | Critical | Pass |
| TST-SEC-09 | REQ-007-03 | SEC-007-02 | Security | Critical | Pass |
| TST-SEC-10 | REQ-007-01 | SEC-007-03 | Security | High | Pass |
| TST-SEC-11 | REQ-007-02 | SEC-007-04 | Security | High | Pass |
| TST-SEC-12 | REQ-007-02 | SEC-007-05 | Security | High | Pass |
| TST-SEC-13 | REQ-007-02 | SEC-007-06 | Security | Medium | Pass |
| TST-SEC-14 | REQ-008-01 | SEC-008-01 | Security | Critical | Pass |
| TST-SEC-15 | REQ-008-01 | SEC-008-03 | Security | High | Pass |
| TST-SEC-16 | REQ-009-01 | SEC-009-01 | Security | Critical | Pass |
| TST-SEC-17 | REQ-009-02 | SEC-009-02 | Security | High | Pass |
| TST-SEC-18 | REQ-009-01 | SEC-009-03 | Security | High | Pass |
| TST-SEC-19 | REQ-008-01 | SEC-008-02 | Security | Medium | Pass |
| TST-010-01 | REQ-010-01 | AC-010-01 | Integration | High | 미실행 |
| TST-010-02 | REQ-010-01 | AC-010-01 | Integration | High | 미실행 |
| TST-010-03 | REQ-010-02 | AC-010-02 | E2E | High | 미실행 |
| TST-010-04 | REQ-010-03 | AC-010-03 | E2E | High | 미실행 |
| TST-011-01 | REQ-011-01 | AC-011-01 | E2E | Critical | 미실행 |
| TST-011-02 | REQ-011-02 | AC-011-02 | E2E | Critical | 미실행 |
| TST-011-03 | REQ-011-03 | AC-011-03 | E2E | High | 미실행 |
| TST-012-01 | REQ-012-02 | AC-012-02 | Integration | Critical | 미실행 |
| TST-012-02 | REQ-012-02 | AC-012-02 | Integration | Critical | 미실행 |
| TST-012-03 | REQ-012-01, REQ-012-03 | AC-012-01, AC-012-03 | E2E | Critical | 미실행 |
| TST-012-04 | REQ-012-03 | AC-012-03 | E2E | High | 미실행 |
| TST-013-01 | REQ-013-01 | AC-013-01 | Integration | Critical | 미실행 |
| TST-013-02 | REQ-013-01 | AC-013-01 | Integration | Critical | 미실행 |
| TST-013-03 | REQ-013-01 | AC-013-01 | Integration | Critical | 미실행 |
| TST-013-04 | REQ-013-02 | AC-013-01 | Integration | High | 미실행 |
| TST-013-05 | REQ-013-03 | AC-013-02 | Integration | Critical | 미실행 |
| TST-013-06 | REQ-013-03 | AC-013-02 | Integration | High | 미실행 |
| TST-013-07 | REQ-013-03 | AC-013-02 | Integration | High | 미실행 |
| TST-013-08 | REQ-013-04 | AC-013-04 | Integration | High | 미실행 |
| TST-SEC-20 | REQ-012-02 | SEC-012-01 | Security | High | 미실행 |
| TST-SEC-21 | REQ-012-02 | SEC-012-02 | Security | High | 미실행 |
| TST-SEC-22 | REQ-012-02 | SEC-012-03 | Security | Medium | 미실행 |
| TST-SEC-23 | REQ-013-01 | SEC-013-01 | Security | High | 미실행 |
| TST-SEC-24 | REQ-013-03 | SEC-013-02 | Security | High | 미실행 |
| TST-SEC-25 | REQ-013-01 | SEC-013-03 | Security | Medium | 미실행 |
| TST-SEC-26 | REQ-013-01 | SEC-013-04 | Security | Medium | 미실행 |
| TST-004-04 | REQ-004-04 | AC-004-04 | E2E | Critical | 미실행 |
| TST-004-05 | REQ-004-04 | AC-004-04 | E2E | High | 미실행 |
| TST-004-06 | REQ-004-05 | AC-004-05 | Integration | Critical | 미실행 |
| TST-004-07 | REQ-004-05 | AC-004-05 | Integration | High | 미실행 |
| TST-004-08 | REQ-004-06 | AC-004-06 | Integration | Critical | 미실행 |
| TST-004-09 | REQ-004-06 | AC-004-06 | E2E | High | 미실행 |
| TST-009-08 | REQ-009-04 | AC-009-04 | Integration | Critical | 미실행 |
| TST-009-09 | REQ-009-04 | AC-009-04 | Integration | High | 미실행 |
| TST-SEC-27 | REQ-004-04 | SEC-004-01 | Security | High | 미실행 |
