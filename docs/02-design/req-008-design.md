# REQ-008 설계 문서 — 인라인 편집 서버 동기화

> Gate 2 — Architect 작성
> 전체 설계: `req-008-009-design.md` 참조

---

## 개요

인라인 편집 시 Zustand 스토어만 갱신되고 서버 state가 갱신되지 않는 문제를 해결한다.
`InlineEditRequest` 모델과 `patch_detail()` 함수가 이미 구현되어 있으므로 라우터 추가와 프론트엔드 API 연결만 필요하다.

---

## 변경 대상 파일

| 파일 경로 | 변경 유형 | 내용 |
|----------|----------|------|
| `backend/app/routers/detail.py` | 신규 | `PATCH /api/v1/detail/{id}` 엔드포인트 |
| `backend/app/main.py` | 수정 | detail 라우터 등록 |
| `frontend/src/api/index.ts` | 수정 | `patchDetailReq()` 함수 추가 |
| `frontend/src/store/useAppStore.ts` | 수정 | 인라인 편집 시 API 호출 연결 |

### 불변 파일

| 파일 경로 | 이유 |
|----------|------|
| `backend/app/models/api.py` | `InlineEditRequest` 모델 이미 구현 완료 |
| `backend/app/state.py` | `patch_detail()` 함수 이미 구현 완료 |

---

## API 설계

| Method | Path | 요청 바디 | 성공 응답 | 실패 응답 |
|--------|------|---------|---------|---------|
| PATCH | `/api/v1/detail/{id}` | `InlineEditRequest` | `DetailRequirement` (200) | `ErrorResponse` (404 / 422) |

### 요청 스키마

```json
{
  "detail_id": "REQ-001-02",
  "field": "content",
  "value": "수정된 내용 텍스트"
}
```

`field`는 `Literal["name", "content", "category"]`로 제한 (이미 모델에 정의됨).
경로 파라미터 `{id}`를 권위 있는 식별자로 사용하고 `patch_detail()`에 전달한다.

### 응답 상태 코드

| 코드 | 조건 |
|------|------|
| 200 | 수정 성공 — `DetailRequirement` 반환 |
| 404 | 해당 id 없음 — `patch_detail()` → `False` |
| 422 | Pydantic 유효성 실패 — field 범위 외 |

---

## 데이터 흐름

```
셀 blur 이벤트
  → api/index.ts patchDetailReq(id, field, value)
      → PATCH /api/v1/detail/{id}
          → state.patch_detail(id, field, value)
  → 성공 응답 수신 후 Zustand 스토어 갱신
  → 실패 시 setError(), 스토어 갱신 없음
```

프론트엔드는 **비낙관적 업데이트** 방식으로 구현한다 — 서버 응답 확인 후 스토어 갱신 (AC-008-03).

---

## 단위 테스트 ID

| UT-ID | 대상 | 설명 |
|-------|------|------|
| UT-008-01 | `PATCH /api/v1/detail/{id}` | 유효 요청 시 200 + 수정된 항목 반환 |
| UT-008-02 | `PATCH /api/v1/detail/{id}` | 존재하지 않는 id → 404 |
| UT-008-03 | `PATCH /api/v1/detail/{id}` | 허용 범위 외 field → 422 |
| UT-008-04 | `PATCH /api/v1/detail/{id}` | 수정 후 state 목록에 값 반영 확인 |
| UT-008-05 | `PATCH /api/v1/detail/{id}` | 수정 후 `is_modified = true` |
| UT-008-06 | `patchDetailReq()` (프론트엔드) | 정상 응답 시 `DetailRequirement` 반환 |
| UT-008-07 | `patchDetailReq()` (프론트엔드) | 서버 404 → 예외 throw |
| UT-008-08 | `useAppStore` | API 성공 후 스토어 값 갱신 확인 |
| UT-008-09 | `useAppStore` | API 실패 시 스토어 불변, 에러 상태 설정 |

---

## 보안 고려사항

| SEC-ID | 위협 | 대응 |
|--------|------|------|
| SEC-008-01 | 임의 필드 덮어쓰기 | `Literal["name","content","category"]` 제한 (이미 구현) |
| SEC-008-02 | 대량 편집 공격 | 단일 사용자 로컬 도구 — 멀티유저 확장 시 Rate Limiting 검토 |
| SEC-008-03 | 초대형 value 입력 | `value` 필드 최대 길이 제한 추가 권장 (5000자 기준) |
