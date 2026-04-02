# 변경 관리 프로세스

요구사항 추가/수정/삭제 시 어떤 문서를 어떤 순서로 고쳐야 하는지 정의한다.

---

## 변경 유형별 처리

### 1. 신규 REQ 추가

| 순서 | 문서 | 작업 | 담당 |
|------|------|------|------|
| 1 | `docs/01-requirements/REQUIREMENTS.md` | REQ-NNN-NN + AC 추가 | PM |
| 2 | `docs/TRACEABILITY.md` | 신규 행 추가 (설계/테스트 컬럼은 빈칸) | PM |
| 3 | `docs/02-design/req-NNN-design[-vN].md` | 설계 문서 작성 | Architect |
| 4 | `docs/TRACEABILITY.md` | 설계 문서 컬럼 채움 | Architect |
| 5 | `docs/03-test-plan/tst-NNN.md` + `TEST_PLAN.md` | TST-ID 추가 | QA |
| 6 | `docs/TRACEABILITY.md` | 테스트 컬럼 채움 | QA |
| 7 | 소스 코드 | 구현 | Developer |
| 8 | `docs/04-review/req-NNN-review.md` | 리뷰 결과 | QA |
| 9 | `docs/TRACEABILITY.md` | 리뷰 문서 컬럼 채움 | QA |

---

### 2. 기존 REQ 수정

| 순서 | 문서 | 작업 | 담당 |
|------|------|------|------|
| 1 | `docs/01-requirements/REQUIREMENTS.md` | 해당 REQ-NNN-NN 내용 수정, 상태 → `수정예정` | PM |
| 2 | `docs/TRACEABILITY.md` | 해당 행 설계/테스트/리뷰 컬럼 → `수정예정` 표시 | PM |
| 3 | `docs/02-design/req-NNN-design-vN.md` | 변경분만 담은 새 버전 파일 작성 | Architect |
| 4 | `docs/TRACEABILITY.md` | 설계 컬럼을 새 파일명으로 교체 | Architect |
| 5 | `docs/03-test-plan/tst-NNN.md` | 해당 TST-ID 덮어쓰기 (현재 요구사항 기준) | QA |
| 6 | `docs/TRACEABILITY.md` | 테스트 컬럼 업데이트 | QA |
| 7 | 소스 코드 | 수정 구현 | Developer |
| 8 | `docs/04-review/req-NNN-review.md` | 리뷰 결과 갱신 | QA |
| 9 | `docs/TRACEABILITY.md` | 리뷰 컬럼 업데이트 | QA |

---

### 3. REQ 삭제

| 순서 | 문서 | 작업 | 담당 |
|------|------|------|------|
| 1 | `docs/01-requirements/REQUIREMENTS.md` | 해당 REQ 상태 → `삭제됨` (행 유지) | PM |
| 2 | `docs/TRACEABILITY.md` | 해당 행 삭제 | PM |
| 3 | `docs/03-test-plan/tst-NNN.md` + `TEST_PLAN.md` | 해당 TST-ID 제거 | QA |
| 4 | 소스 코드 | 관련 코드 제거 | Developer |
| 5 | `docs/04-review/` | 해당 리뷰 파일 보존 (히스토리) | - |

> 설계 문서는 삭제하지 않고 보존한다. git 히스토리와 함께 의사결정 근거로 남긴다.

---

## 문서 간 의존 순서

```
REQUIREMENTS.md
    ↓
TRACEABILITY.md (설계 컬럼 빈칸)
    ↓
req-NNN-design[-vN].md
    ↓
TRACEABILITY.md (설계 컬럼 채움)
    ↓
tst-NNN.md + TEST_PLAN.md
    ↓
TRACEABILITY.md (테스트 컬럼 채움)
    ↓
소스 코드
    ↓
req-NNN-review.md
    ↓
TRACEABILITY.md (리뷰 컬럼 채움)
```

---

## 핵심 원칙

- **테스트(TST)는 항상 현재 요구사항 기준으로 덮어쓴다** — 이전 버전 테스트는 git이 보관
- **설계 문서는 버전 파일로 추가한다** — 기존 파일은 건드리지 않음 (req-NNN-design-v2.md)
- **TRACEABILITY.md는 현재 유효한 상태만 반영한다** — 히스토리는 git
- **REQ는 삭제하지 않고 `삭제됨` 상태로 남긴다** — 번호 재사용 금지
