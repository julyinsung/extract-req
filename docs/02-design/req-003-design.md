# REQ-003 설계 — 결과 화면 표시 (테이블 UI)

> Gate 2a/2c — 담당 범위: REQ-003-01 ~ REQ-003-04

---

## React 컴포넌트

### `OriginalReqTable`

```typescript
// props
interface OriginalReqTableProps {
  rows: OriginalRequirement[]
}
```

- 원본 요구사항 4컬럼(ID / 분류 / 명칭 / 내용) 읽기 전용 테이블
- 편집 불가 — 원본 데이터는 수정하지 않는다는 UX 원칙
- 데이터 없을 때 빈 상태 메시지 표시

### `DetailReqTable`

```typescript
// 스토어 직접 접근 (props 없음)
// useAppStore에서: detailReqs, isGenerating, patchDetailReq
```

- AI 생성 중(`isGenerating`) SSE `item` 이벤트 수신 시 행 동적 추가
- 셀 클릭 → `InlineEditCell`로 전환
- `isGenerating` 동안 편집 비활성화 (생성 중 충돌 방지)
- 채팅 패치로 변경된 행: 3초간 노란 배경 강조 후 원복

### `InlineEditCell`

```typescript
interface InlineEditCellProps {
  value: string
  field: "name" | "content" | "category"
  detailId: string
  onSave: (field: string, value: string) => void
}
```

- 셀 클릭 → `<input>` (name/category) 또는 `<textarea>` (content)로 전환
- `blur` 이벤트에서 `patchDetailReq()` + 백엔드 `PATCH /api/v1/details/{id}` 호출
- `Escape` 키 → 변경 취소, 원래 값으로 복원

### `ReqTableRow`

- 원본/상세 행 유형에 따라 배경색 CSS 클래스 적용
- `is_modified = true` 인 상세 행: 수정 마크 표시

---

## Zustand 전역 스토어

```typescript
// src/store/useAppStore.ts

interface AppState {
  sessionId: string | null
  originalReqs: OriginalRequirement[]
  detailReqs: DetailRequirement[]
  chatHistory: ChatMessage[]
  isUploading: boolean
  isGenerating: boolean
  isChatting: boolean
  error: string | null
}

interface AppActions {
  setSessionId(id: string): void
  setOriginalReqs(reqs: OriginalRequirement[]): void
  appendDetailReq(req: DetailRequirement): void
  patchDetailReq(id: string, field: string, value: string): void
  appendChatMessage(msg: ChatMessage): void
  setError(msg: string | null): void
  reset(): void
}
```

- `persist` 미사용 — 페이지 새로고침 시 초기화는 허용된 동작
- Context API 대신 Zustand 채택 — 불필요한 리렌더링 최소화

---

## 디자인 토큰 (시각적 구분)

| 항목 | 값 | 적용 대상 |
|------|-----|---------|
| Primary | `#2563EB` | 버튼, 헤더 강조 |
| 원본 행 배경 | `#FFFFFF` | OriginalReqTable, 2단계 엑셀 원본 행 |
| 상세 행 배경 | `#F0F9FF` | DetailReqTable 행 |
| 수정 행 강조 | `#FEF9C3` | 채팅 패치 후 3초 애니메이션 |
| 헤더 배경 | `#4472C4` | 테이블/엑셀 헤더 |
| 원본 ID 폰트 | Bold | REQ ID 컬럼 |
| 상세 ID 들여쓰기 | 16px padding-left | 계층 구조 시각화 |

---

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-003-01 | `OriginalReqTable` | rows 5건 → 테이블 행 5개 렌더링 |
| UT-003-02 | `DetailReqTable` | `appendDetailReq()` 3회 → 행 3개 추가 |
| UT-003-03 | `InlineEditCell` | 셀 클릭 → input 렌더링, blur → `patchDetailReq` 호출 |
| UT-003-04 | 시각 구분 | 원본/상세 행 배경색 CSS 클래스 올바른 적용 |
| UT-003-05 | 수정 하이라이트 | patch 이벤트 수신 → 해당 행 강조 CSS 적용 |
