# REQ-013 설계 문서 — 파일 스냅샷 저장 및 복원

## 개요

- **REQ 그룹**: REQ-013 — 파일 스냅샷 저장 및 복원
- **설계 방식**: 인메모리 싱글턴 + 파일 동기화 (DB 미도입)
- **핵심 결정사항**: 기존 `state.py` 싱글턴 구조를 보존하면서 변경 유발 지점(추가/삭제/수정)에서만 `session_snapshot.json` 덮어쓰기를 수행하고, 서버 기동 시 `lifespan` 이벤트에서 파일을 읽어 인메모리 state를 복원한다.

---

## 시스템 구조

```
[서버 기동]
  ↓
main.py (lifespan startup)
  → snapshot.load_snapshot()
      → backend/data/session_snapshot.json 존재 여부 확인
          파일 있음 → JSON 역직렬화 → state 복원 (set_original, set_detail 호출)
          파일 없음 → 빈 SessionState로 시작 (기존 동작 유지)
  ↓
[정상 서비스]

[상세요구사항 변경 발생]
  ↓
  ┌─ PATCH  /api/v1/detail/{id}   → state.patch_detail()       ┐
  ├─ DELETE /api/v1/detail/{id}   → state.delete_detail()      ├→ snapshot.save_snapshot()
  └─ /api/generate 완료 (set_detail 호출 시)                   ┘    → 덮어쓰기
       → state.set_detail()
           → snapshot.save_snapshot()

[저장 결과]
  backend/data/session_snapshot.json  ← 최신 1개만 유지 (덮어쓰기)
```

### 변경 유발 지점 요약

| 이벤트 | 호출 경로 | 스냅샷 저장 위치 |
|--------|-----------|-----------------|
| 상세요구사항 생성 완료 | `generate` 라우터 → `state.set_detail()` | `set_detail()` 내부 |
| 인라인 PATCH 수정 | `detail` 라우터 → `state.patch_detail()` | `patch_detail()` 내부 |
| 상세요구사항 삭제 | `detail` 라우터 → `state.delete_detail()` | `delete_detail()` 내부 |
| REPLACE 교체 | `chat_service_sdk.py` → `state.replace_detail_group()` | `replace_detail_group()` 내부 |

---

## 모듈/컴포넌트 설계

### snapshot 모듈 (신규)

- **위치**: `backend/app/snapshot.py`
- **책임**: `session_snapshot.json` 파일의 저장(직렬화)과 복원(역직렬화)을 전담한다. `state.py`와 `main.py`가 이 모듈에 의존하며, 반대 방향 의존성은 없다.
- **인터페이스**:
  ```
  SNAPSHOT_PATH: Path  — 저장 경로 상수 (backend/data/session_snapshot.json)

  save_snapshot() -> None
      현재 state를 JSON으로 직렬화하여 SNAPSHOT_PATH에 원자적으로 저장한다.
      실패 시 예외를 억제하고 로그만 출력 — 스냅샷 저장 실패가 API 응답을 막아서는 안 된다.

  load_snapshot() -> bool
      SNAPSHOT_PATH 파일을 읽어 state를 복원한다.
      복원 성공 시 True, 파일 없거나 파싱 실패 시 False.
      파싱 실패 시 예외를 억제하고 False 반환 — 손상된 파일이 서버 기동을 막아서는 안 된다.
  ```
- **직렬화 대상**: `SessionState`의 `original_requirements`와 `detail_requirements` 두 필드만 저장한다.
  - `session_id`, `created_at`은 재시작 후 새 값으로 발급한다 (복원 불필요).
  - `chat_messages`, `sdk_sessions`는 세션 의존 데이터이므로 복원하지 않는다 (sdk session_id는 재생성 시 갱신됨).
- **스냅샷 JSON 구조**:
  ```json
  {
    "original_requirements": [ ...OriginalRequirement 목록... ],
    "detail_requirements":   [ ...DetailRequirement 목록... ]
  }
  ```
- **저장 경로**: `backend/data/session_snapshot.json`
  - `backend/data/` 디렉토리는 기존에 존재하며(`tmp/` 하위 디렉토리 확인), 별도 디렉토리 생성 불필요.
  - `save_snapshot()` 최초 호출 시 `backend/data/` 디렉토리가 없을 경우 생성 후 저장한다 (`mkdir(parents=True, exist_ok=True)`).
- **원자적 쓰기**: 동일 디렉토리 내 임시 파일(`session_snapshot.tmp`)에 쓴 후 `rename`으로 교체한다. 쓰기 도중 서버가 종료돼도 이전 스냅샷이 손상되지 않는다.
  - Windows에서는 `os.replace()`가 원자성을 보장하지 않을 수 있으나, 단일 사용자 로컬 도구이므로 허용 가능한 위험 수준이다.
- **스레드 안전성**: `save_snapshot()`은 `state.py`의 `_lock` 보호 하에 호출된다. 모듈 자체에 별도 락을 추가하지 않는다.
- **결정 근거**: 스냅샷 책임을 별도 모듈로 분리하면 `state.py`가 파일 I/O에 직접 의존하지 않게 되어 단위 테스트에서 파일 시스템 없이 `state.py`를 테스트할 수 있다. `snapshot.py`는 파일 경계만 테스트한다.

---

### state.py 변경 (기존 모듈 수정)

REQ-009 설계(`req-004-009-design.md`)에서 이미 확정된 변경 사항 위에 REQ-013 변경을 추가한다.

REQ-009 이후 `state.py`의 확정 인터페이스:
- `get_sdk_session_id(req_group: str) -> str | None`
- `set_sdk_session_id(req_group: str, session_id: str) -> None`
- `get_original_by_group(req_group: str) -> OriginalRequirement | None`
- `get_detail_by_group(req_group: str) -> list[DetailRequirement]`
- `replace_detail_group(req_group: str, items: list[DetailRequirement]) -> None`

**REQ-013 추가 변경:**

#### `set_detail()` 수정
- **책임**: AI 생성 상세요구사항 저장 및 상태 전이 (기존) + 스냅샷 저장 트리거 (신규)
- **인터페이스**: `set_detail(reqs: list[DetailRequirement]) -> None` (시그니처 변경 없음)
- **제약**: 기존 `_lock` 블록 이후 `snapshot.save_snapshot()` 호출. `_lock` 블록 외부에서 호출하여 데드락을 방지한다. `save_snapshot()` 예외는 이미 억제되므로 `set_detail()` 호출자에게 전파되지 않는다.

#### `patch_detail()` 수정
- **책임**: 단일 필드 수정 (기존) + 스냅샷 저장 트리거 (신규)
- **인터페이스**: `patch_detail(req_id: str, field: str, value: str) -> bool` (시그니처 변경 없음)
- **제약**: 수정 성공(`True` 반환) 시에만 `snapshot.save_snapshot()` 호출. 실패 시(`False`) 저장하지 않는다. `_lock` 블록 외부에서 호출한다.

#### `delete_detail()` 신규 추가
- **책임**: 특정 id의 상세요구사항을 인메모리 state에서 제거한다.
- **인터페이스**: `delete_detail(req_id: str) -> bool`
  - 삭제 성공 시 `True`, 해당 id가 없으면 `False`.
- **제약**: `_lock` 보호. 삭제 성공 시 `_lock` 블록 외부에서 `snapshot.save_snapshot()` 호출.
- **결정 근거**: 현재 `state.py`에 삭제 함수가 없다. REQ-013-01의 "삭제 시 스냅샷 저장" 요구사항을 충족하려면 삭제를 state 계층에서 처리해야 한다. `detail.py` 라우터가 직접 리스트를 조작하면 스레드 안전성과 스냅샷 동기화가 깨진다.

#### `replace_detail_group()` 수정 (REQ-009 설계에서 신규, REQ-013에서 스냅샷 추가)
- **제약**: 교체 성공 후 `_lock` 블록 외부에서 `snapshot.save_snapshot()` 호출.

#### `reset_session()` 관련 주의
- `reset_session()`은 새 HWP 업로드 시 state 전체를 초기화한다.
- REQ-013 범위에서 `reset_session()` 호출 시 스냅샷을 삭제하거나 덮어쓰지 않는다. 스냅샷은 다음 `set_detail()` 호출 시(새 생성 완료 후) 갱신된다.
- 결정 근거: 새 HWP 업로드 후 생성 전에 서버가 재시작되면 이전 스냅샷으로 복원되는 엣지 케이스가 존재하나, 이는 "생성 완료 전" 상태이므로 허용 가능하다. 복원 후 사용자가 다시 생성하면 스냅샷이 최신화된다.

---

### detail.py 라우터 변경 (기존 모듈 수정)

#### `DELETE /api/v1/detail/{id}` 신규 엔드포인트 추가

- **책임**: 특정 id의 상세요구사항을 삭제하고 결과를 반환한다.
- **인터페이스**:
  ```
  DELETE /api/v1/detail/{id}
    요청: 경로 파라미터 id (str)
    응답 200: {"deleted_id": id}
    응답 404: ErrorResponse (code: "NOT_FOUND")
  ```
- **처리 흐름**: `state.delete_detail(id)` 호출 → False이면 404, True이면 200 반환.
- **제약**: 스냅샷 저장은 `state.delete_detail()` 내부에서 처리한다. 라우터는 저장 여부를 인지하지 않는다 (관심사 분리).
- **결정 근거**: 현재 `detail.py`에 삭제 엔드포인트가 없으나 AC-013-01이 "삭제 발생 시 스냅샷 저장"을 명시하므로 신규 추가가 필요하다. 삭제 API가 없으면 프론트엔드에서 삭제 기능을 구현할 수 없다.

---

### main.py 변경 (기존 모듈 수정)

- **책임**: 서버 기동 시 스냅샷 복원을 트리거한다.
- **변경 내용**: `lifespan` 컨텍스트 매니저를 추가하여 startup 시 `snapshot.load_snapshot()`을 호출한다.
- **인터페이스**:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      snapshot.load_snapshot()   # startup: 스냅샷 복원 시도
      yield
      # shutdown: 별도 처리 없음 (파일은 변경 시마다 저장됨)
  ```
- **제약**:
  - 현재 `main.py`는 `lifespan`이 없다. `FastAPI(lifespan=lifespan)` 인자로 전달한다.
  - `load_snapshot()` 실패(파일 없음 또는 파싱 오류) 시 서버 기동을 중단하지 않는다. 빈 state로 정상 기동한다.
  - startup 완료 로그에 복원 성공/실패 여부를 출력한다.

---

## API 설계

REQ-013 신규 엔드포인트:

| Method | Path | 설명 | 인증 | 요청 | 응답 |
|--------|------|------|------|------|------|
| DELETE | `/api/v1/detail/{id}` | 특정 상세요구사항 삭제 | 없음 | 경로 파라미터 `id: str` | `{"deleted_id": str}` / 404 |

기존 엔드포인트는 REQ-013으로 인한 시그니처 변경 없음. 스냅샷 저장은 내부 동작이며 API 응답에 영향을 주지 않는다.

---

## 디렉토리 구조

```
backend/
├── app/
│   ├── main.py               # [수정] lifespan startup에 load_snapshot() 추가
│   ├── state.py              # [수정] set_detail, patch_detail, replace_detail_group에
│   │                         #        save_snapshot() 트리거 추가; delete_detail() 신규
│   ├── snapshot.py           # [신규] save_snapshot(), load_snapshot() 전담 모듈
│   └── routers/
│       └── detail.py         # [수정] DELETE /api/v1/detail/{id} 엔드포인트 추가
├── data/
│   ├── tmp/                  # 기존 디렉토리
│   └── session_snapshot.json # [런타임 생성] 스냅샷 파일 (gitignore 대상)
└── tests/
    └── test_snapshot.py      # [신규] snapshot 모듈 단위 테스트
```

`.gitignore` 추가 대상:
```
backend/data/session_snapshot.json
backend/data/session_snapshot.tmp
```

---

## 데이터 흐름: 스냅샷 저장

```
[변경 발생]
state.set_detail() / patch_detail() / delete_detail() / replace_detail_group()
  └─ _lock 블록: 인메모리 state 갱신
  └─ _lock 블록 해제 후: snapshot.save_snapshot() 호출
      └─ state.get_session() → SessionState 조회
      └─ {original_requirements, detail_requirements} 직렬화
      └─ backend/data/session_snapshot.tmp 에 쓰기
      └─ os.replace(tmp → session_snapshot.json)
      └─ 실패 시: 예외 억제 + stderr 로그 출력
```

## 데이터 흐름: 스냅샷 복원

```
[서버 기동]
lifespan startup → snapshot.load_snapshot()
  └─ backend/data/session_snapshot.json 존재 확인
      없음 → False 반환, 빈 state로 기동
      있음 → JSON 파싱
          파싱 실패 → False 반환, 빈 state로 기동 (손상 파일 무시)
          파싱 성공 →
              state.set_original(original_requirements) — status: "parsed"로 전이
              state.set_detail(detail_requirements)     — status: "generated"로 전이
                  ※ set_detail 내부에서 save_snapshot()이 다시 호출되나,
                    복원 직후 동일 데이터로 덮어쓰기이므로 부작용 없음.
              True 반환
```

**set_detail 재귀 저장 주의**: `load_snapshot()` 내에서 `state.set_detail()`을 호출하면 `save_snapshot()`이 다시 트리거된다. 이는 복원 직후 동일 데이터를 재저장하는 것이므로 무한 루프가 아니며 기능상 무해하다. 설계를 단순하게 유지하기 위해 허용한다.

---

## 단위 테스트 ID 사전 할당

| UT-ID | 대상 | 설명 | REQ-ID |
|-------|------|------|--------|
| UT-013-01 | `snapshot.save_snapshot()` | 변경 후 `session_snapshot.json`이 생성되고 `original_requirements`와 `detail_requirements` 두 키를 포함함 | REQ-013-01 |
| UT-013-02 | `snapshot.save_snapshot()` | 두 번 연속 호출 시 파일이 최신 상태 1개로 덮어쓰임 (이전 데이터 잔존 없음) | REQ-013-02 |
| UT-013-03 | `snapshot.load_snapshot()` | 유효한 `session_snapshot.json` 존재 시 `state.get_detail()`이 복원된 항목을 반환함 | REQ-013-03 |
| UT-013-04 | `snapshot.load_snapshot()` | `session_snapshot.json`이 없으면 `False`를 반환하고 state가 빈 상태임 | REQ-013-03 |
| UT-013-05 | `snapshot.load_snapshot()` | `session_snapshot.json`이 손상된 JSON이면 `False`를 반환하고 서버 기동을 중단하지 않음 | REQ-013-03 |
| UT-013-06 | `state.patch_detail()` | 수정 성공 후 `session_snapshot.json`의 해당 항목 필드가 갱신된 값으로 저장됨 | REQ-013-01 |
| UT-013-07 | `state.delete_detail()` | 존재하는 id 삭제 시 `True` 반환, 이후 `state.get_detail()`에 해당 항목이 없음 | REQ-013-01 |
| UT-013-08 | `state.delete_detail()` | 존재하지 않는 id 삭제 시 `False` 반환, state 변경 없음 | REQ-013-01 |
| UT-013-09 | `state.delete_detail()` | 삭제 성공 후 `session_snapshot.json`에 해당 항목이 포함되지 않음 | REQ-013-01 |
| UT-013-10 | `state.set_detail()` | 호출 후 `session_snapshot.json`의 `detail_requirements` 항목 수가 인메모리 state와 일치함 | REQ-013-01 |
| UT-013-11 | `snapshot.save_snapshot()` | 파일 쓰기 실패 시(권한 오류 등) 예외를 억제하고 호출자에게 전파하지 않음 | REQ-013-04 |
| UT-013-12 | `DELETE /api/v1/detail/{id}` | 존재하는 id로 DELETE 호출 시 200과 `{"deleted_id": id}` 반환 | REQ-013-01 |
| UT-013-13 | `DELETE /api/v1/detail/{id}` | 존재하지 않는 id로 DELETE 호출 시 404와 `NOT_FOUND` 에러 코드 반환 | REQ-013-01 |
| UT-013-14 | `snapshot.load_snapshot()` | 복원 후 `state.get_original()`이 스냅샷의 `original_requirements` 목록을 반환함 | REQ-013-03 |

---

## 보안 고려사항

| SEC-ID | 위협 | 대응 방안 | OWASP |
|--------|------|----------|-------|
| SEC-013-01 | 스냅샷 파일 경로 조작 — 환경변수나 설정으로 경로를 주입하여 임의 경로에 파일 쓰기 | `SNAPSHOT_PATH`를 `snapshot.py` 내부 상수로 고정한다. 외부 입력으로 경로를 변경하는 인터페이스를 제공하지 않는다. | A03 Injection |
| SEC-013-02 | 스냅샷 파일 위변조 — 공격자가 `session_snapshot.json`을 수정하여 서버 복원 시 악성 데이터 주입 | `load_snapshot()` 시 Pydantic 모델(`OriginalRequirement`, `DetailRequirement`)로 역직렬화하여 스키마 검증을 통과한 데이터만 state에 적재한다. 파싱 실패 시 전체 복원을 취소하고 빈 state로 기동한다. | A08 Software and Data Integrity Failures |
| SEC-013-03 | 스냅샷 파일 과대 성장 — 대량 항목이 포함된 state를 반복 저장하여 디스크 고갈 | 단일 사용자 로컬 도구이며 최신 1개 파일만 유지한다. 별도 크기 제한은 두지 않으나, `set_detail()` 단계에서 항목 수 상한이 이미 존재한다면 그 제약이 스냅샷에도 자동 적용된다. | A05 Security Misconfiguration |
| SEC-013-04 | 임시 파일 잔존 — 쓰기 중 서버 종료 시 `session_snapshot.tmp`가 남아 다음 기동에서 오염 | `load_snapshot()`은 `.tmp` 파일을 읽지 않고 `.json` 파일만 읽는다. 잔존 `.tmp` 파일은 다음 저장 시 덮어쓰여 자동 정리된다. | A05 Security Misconfiguration |

---

## 트레이드오프 기록

| 결정 | 채택 방안 | 포기한 대안 | 이유 |
|------|----------|------------|------|
| 저장 타이밍 | 변경 즉시 동기 저장 (인라인) | 주기적 백그라운드 저장 | 단순한 구현, 타이머/스케줄러 의존성 없음. 단일 사용자 도구에서 지연 저장은 복잡도 대비 이점 없음 |
| 저장 대상 필드 | `original_requirements` + `detail_requirements`만 저장 | `SessionState` 전체 저장 | `session_id`, `created_at`은 재시작 후 재발급하는 것이 자연스럽다. `chat_messages`는 세션 컨텍스트이므로 재시작 후 의미 없다. `sdk_sessions`는 외부 서비스(Claude SDK) 세션이므로 재시작 후 무효화된다 |
| 복원 위치 | `lifespan` startup | `get_session()` 최초 호출 시 지연 복원 | `lifespan`이 명시적이고 테스트가 용이하다. 지연 복원은 경쟁 조건 가능성이 있다 |
| 스냅샷 모듈 분리 | `snapshot.py` 별도 모듈 | `state.py` 내에 직접 구현 | `state.py`가 파일 I/O에 직접 의존하면 단위 테스트에서 파일 시스템 모킹이 필요하다. 분리하면 각 모듈을 독립적으로 테스트할 수 있다 |
