# REQ-008 설계 문서 — 인라인 편집 서버 동기화

> Gate 2 — Architect 작성

---

## 개요

인라인 편집 시 Zustand 스토어만 갱신되고 서버 state가 갱신되지 않는 문제를 해결한다.
`InlineEditRequest` 모델과 `patch_detail()` 함수가 이미 구현되어 있으므로 **라우터 추가(백엔드)** 와 **API 호출 연결(프론트엔드)** 만 필요하다.

---

## 변경 파일 요약

| 담당 | 파일 | 변경 유형 |
|------|------|----------|
| **백엔드** | `backend/app/routers/detail.py` | 신규 생성 |
| **백엔드** | `backend/app/main.py` | 수정 (라우터 등록) |
| **프론트엔드** | `frontend/src/api/index.ts` | 수정 (API 함수 추가) |
| **프론트엔드** | `frontend/src/store/useAppStore.ts` | 수정 (비동기 호출 연결) |
| 불변 | `backend/app/models/api.py` | `InlineEditRequest` 이미 정의됨 |
| 불변 | `backend/app/state.py` | `patch_detail()` 이미 구현됨 |

---

## 백엔드 설계

### 새 파일: `backend/app/routers/detail.py`

**책임**: `PATCH /api/v1/detail/{id}` 요청을 받아 `state.patch_detail()`을 호출하고 결과를 반환한다.

#### API 스펙

| 항목 | 값 |
|------|---|
| Method | `PATCH` |
| Path | `/api/v1/detail/{id}` |
| 요청 바디 | `InlineEditRequest` |
| 성공 응답 | `DetailRequirement` (200) |
| 실패 응답 | `ErrorResponse` (404 / 422) |

#### 요청 바디 (`InlineEditRequest` — 기존 모델 재사용)

```json
{
  "detail_id": "REQ-001-02",
  "field": "content",
  "value": "수정된 내용 텍스트"
}
```

- `field`는 `Literal["name", "content", "category"]`로 제한됨 (Pydantic이 422 자동 반환)
- 경로 파라미터 `{id}`를 권위 있는 식별자로 사용 — `patch_detail(req_id=id)`에 전달

#### 응답 상태 코드

| 코드 | 조건 |
|------|------|
| 200 | 수정 성공 — 수정된 `DetailRequirement` JSON 반환 |
| 404 | 해당 id 없음 — `patch_detail()` → `False` 반환 시 |
| 422 | 유효성 실패 — `field` 범위 외, 필드 누락 등 |

#### 성공 응답 예시

```json
{
  "id": "REQ-001-02",
  "parent_id": "REQ-001",
  "category": "기능 요구사항",
  "name": "로그인 기능",
  "content": "수정된 내용 텍스트",
  "order_index": 1,
  "is_modified": true
}
```

---

### 수정 파일: `backend/app/main.py`

기존 라우터 등록 패턴과 동일하게 `detail` 라우터를 추가로 등록한다.

---

### 보안 고려사항 (백엔드)

| SEC-ID | 위협 | 대응 |
|--------|------|------|
| SEC-008-01 | 임의 필드 덮어쓰기 | `Literal["name","content","category"]` 제한 — 이미 구현됨 |
| SEC-008-03 | 초대형 value 입력 | `value` 필드 최대 길이 5000자 제한 추가 권장 |

---

### 단위 테스트 (백엔드)

| UT-ID | 대상 | 설명 |
|-------|------|------|
| UT-008-01 | `PATCH /api/v1/detail/{id}` | 유효 요청 시 200 + 수정된 항목 반환 |
| UT-008-02 | `PATCH /api/v1/detail/{id}` | 존재하지 않는 id → 404 |
| UT-008-03 | `PATCH /api/v1/detail/{id}` | 허용 범위 외 field → 422 |
| UT-008-04 | `PATCH /api/v1/detail/{id}` | 수정 후 `state.get_detail()` 목록에 값 반영 확인 |
| UT-008-05 | `PATCH /api/v1/detail/{id}` | 수정 후 `is_modified = true` 확인 |

---

## 프론트엔드 설계

### 수정 파일: `frontend/src/api/index.ts`

**책임**: `PATCH /api/v1/detail/{id}` 를 호출하는 `patchDetailReq()` 함수를 추가한다.

#### 함수 인터페이스

```typescript
async function patchDetailReq(
  id: string,
  field: 'name' | 'content' | 'category',
  value: string
): Promise<DetailRequirement>
```

- 기존 `uploadHwp()`와 동일하게 axios 사용
- 서버 404 또는 네트워크 오류 시 예외를 throw — 호출자가 catch

---

### 수정 파일: `frontend/src/store/useAppStore.ts`

**책임**: 인라인 편집 저장 시 서버 API를 호출하고 성공 후 스토어를 갱신한다.

#### 변경 방식 — 비낙관적 업데이트 (API 성공 후 스토어 갱신)

낙관적 업데이트(즉시 갱신 후 백그라운드 동기화)는 채팅 AI가 stale 데이터를 볼 위험이 있어 사용하지 않는다 (AC-008-03).

```
셀 blur 이벤트
  → api/index.ts patchDetailReq(id, field, value) 호출
      → 성공: patchDetailReq(id, field, value) 스토어 갱신
      → 실패: setError() 호출, 스토어 갱신 없음
```

현재 `patchDetailReq` 액션은 동기 상태 갱신으로 유지하고, 비동기 API 호출은 컴포넌트(`DetailReqTable`) 또는 별도 헬퍼에서 처리한다.

---

### 보안 고려사항 (프론트엔드)

| SEC-ID | 위협 | 대응 |
|--------|------|------|
| SEC-008-02 | 대량 편집 공격 | 단일 사용자 로컬 도구 — 현재 위험 낮음 |

---

### 단위 테스트 (프론트엔드)

| UT-ID | 대상 | 설명 |
|-------|------|------|
| UT-008-06 | `patchDetailReq()` API 함수 | 정상 응답 시 `DetailRequirement` 반환 |
| UT-008-07 | `patchDetailReq()` API 함수 | 서버 404 → 예외 throw |
| UT-008-08 | `useAppStore` | API 성공 후 스토어 해당 항목 갱신 확인 |
| UT-008-09 | `useAppStore` | API 실패 시 스토어 불변, 에러 상태 설정 확인 |
