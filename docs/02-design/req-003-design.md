# REQ-003 설계 — 결과 화면 표시 (테이블 UI)

> 통합 설계 문서 참조: `req-all-design.md`, `ui-design.md`

## 담당 범위

REQ-003-01 ~ REQ-003-04: 원본/상세 테이블, 동적 행 추가, 인라인 편집, 시각 구분

## React 컴포넌트

| 컴포넌트 | 역할 |
|---------|------|
| `OriginalReqTable` | 파싱 완료 후 원본 요구사항 4컬럼 테이블 표시 |
| `DetailReqTable` | SSE 수신 시 동적 행 추가, 인라인 편집 지원 |
| `ReqTableRow` | 행 단위 렌더링, 편집 상태 관리 |
| `InlineEditCell` | 셀 클릭 → input/textarea 전환, blur 저장 |

## 상태 관리 (Zustand)

```typescript
interface AppStore {
  originalReqs: OriginalRequirement[]   // 파싱 결과
  detailReqs: DetailRequirement[]       // AI 생성 결과
  isGenerating: boolean                 // SSE 수신 중
  editingCell: { rowId: string; col: string } | null
  highlightedRows: Set<string>          // 채팅 수정 후 강조
}
```

## 시각적 구분 (REQ-003-04)

- 원본 행: 흰색 배경 (`#FFFFFF`), 볼드 ID
- 상세 행: 연한 파란 배경 (`#F0F9FF`), 들여쓰기 ID (REQ-001-01)
- 채팅 수정 행: 노란 배경 (`#FEF9C3`), 3초 후 원복 애니메이션

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-003-01 | `OriginalReqTable` | rows prop → 테이블 행 수 일치 |
| UT-003-02 | `DetailReqTable` | SSE item 수신 → 행 동적 추가 |
| UT-003-03 | `InlineEditCell` | 셀 클릭 → 편집 모드 전환, blur → 저장 |
| UT-003-04 | 시각 구분 | 원본/상세 행 배경색 CSS 클래스 확인 |
