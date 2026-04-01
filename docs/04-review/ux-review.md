# UX 리뷰

> 작성일: 2026-04-01
> 검수 방식: 소스코드 정적 분석 (앱 미실행)
> 검수 범위: `frontend/src/` 전체

---

## 판정: PASS (조건부)

필수 Blocker 항목은 없습니다. 단, 아래의 Minor 항목들이 UX 완성도에 영향을 주므로 개선을 권장합니다.

---

## 검수 환경

- 분석 방법: 소스코드 정적 분석 (Playwright 캡처 미수행)
- 분석 대상 파일
  - `frontend/src/App.tsx`
  - `frontend/src/components/UploadPanel.tsx`
  - `frontend/src/components/OriginalReqTable.tsx`
  - `frontend/src/components/DetailReqTable.tsx`
  - `frontend/src/components/ChatPanel.tsx`
  - `frontend/src/components/DownloadBar.tsx`
  - `frontend/src/components/InlineEditCell.tsx`
  - `frontend/src/store/useAppStore.ts`
  - `frontend/src/types/index.ts`
  - `frontend/src/App.css`
  - `frontend/src/index.css`
- 참조 설계: `docs/02-design/ui-design.md`

---

## 필수 검증

| ID | 항목 | 결과 | 근거 |
|----|------|------|------|
| UX-A | 디자인 토큰 준수 | PASS | 색상값이 인라인 스타일로 하드코딩되어 있으나, 적용된 값이 ui-design.md 디자인 토큰과 일치함. primary(#2563EB), success(#059669), error-light(#FEF2F2), row-detail(#F0F9FF), row-highlight(#FEF9C3) 등 주요 토큰값이 설계 문서와 동일하게 사용됨 |
| UX-B | 화면 흐름 | PASS | upload → parsed → generated 단방향 전환이 `useAppStore`의 `phase` 상태로 정확히 제어됨. 설계 flowchart의 세 화면(업로드/테이블/채팅)과 실제 구현의 조건부 렌더링이 일치함. "새 파일 업로드" 버튼으로 S1 복귀 동작도 구현됨 |
| UX-C | 컴포넌트 일관성 | PASS | 두 테이블(OriginalReqTable, DetailReqTable)이 동일한 헤더 배경색(#4472C4)과 TH_STYLE/TD_STYLE 상수를 사용하여 일관된 표 스타일 유지. 버튼의 borderRadius(8px), 색상, fontWeight(600)이 공통 패턴으로 반복됨 |
| UX-D | 핵심 사용성 | PASS | 주요 CTA 흐름(파일 선택 → 업로드 → 생성 → 채팅 → 다운로드)이 각 단계에서 명확하게 표시됨. 비활성화 조건이 올바르게 설정됨(파일 미선택 시 업로드 버튼 비활성, detailReqs 없을 때 채팅 비활성, 생성 중 편집 비활성) |

---

## 권고 검증

| ID | 항목 | 결과 | 개선 제안 |
|----|------|------|---------|
| UX-E | 접근성 | WARN | 주요 항목은 충족하나 일부 미흡 사항 존재 (아래 Minor 항목 3, 4 참조) |
| UX-F | 반응형 | WARN | 모바일/태블릿 브레이크포인트 처리 없음. 채팅 패널이 좁은 화면에서 테이블을 밀어낼 수 있음 (아래 Minor 항목 1 참조) |
| UX-G | 마이크로인터랙션 | WARN | 업로드 버튼의 loading 스피너 없음. 생성 버튼 호버/포커스 스타일 미정의. 에러 배너 닫기 불가 (아래 Minor 항목 2, 5 참조) |
| UX-H | 빈 상태/에지 케이스 | PASS | 빈 테이블 상태("데이터가 없습니다", "상세요구사항이 없습니다") 구현됨. 채팅 빈 상태 안내 메시지 구현됨. 2000자 입력 제한 구현됨 |

---

## 발견 사항

### Blocker (즉시 수정 필요)

없음.

---

### Minor (개선 권장)

**1. 반응형 미지원 — 모바일/태블릿에서 레이아웃 붕괴 가능성**

- 관련 파일: `frontend/src/App.tsx` (line 79~96)
- 문제: `phase !== 'upload'` 상태의 2컬럼 레이아웃(`display: flex, gap: 24`)에 미디어 쿼리가 없음. 채팅 패널 너비가 380px 고정(`width: 380, flexShrink: 0`)이므로 태블릿(768px) 이하에서 테이블 영역이 극도로 좁아지거나 레이아웃이 깨질 수 있음.
- 설계 명세: ui-design.md "반응형 브레이크포인트" — 모바일/태블릿에서 채팅 패널을 테이블 하단에 배치하고 수평 스크롤을 허용하도록 명시.
- 개선안: `App.tsx` flex 컨테이너에 `flexWrap: 'wrap'` 추가 및 ChatPanel에 `@media (max-width: 1024px)` 시 `width: 100%` 적용.

---

**2. 업로드 버튼에 로딩 스피너 없음**

- 관련 파일: `frontend/src/components/UploadPanel.tsx` (line 132~154)
- 문제: `isUploading` 중 버튼 텍스트가 "업로드 중..."으로 변경되지만 시각적 스피너가 없음. 업로드 처리가 길어질 경우 사용자가 진행 중임을 인지하기 어려울 수 있음.
- 설계 명세: ui-design.md Button 컴포넌트 명세의 `loading: boolean — 로딩 스피너 표시` 속성 명시.
- 개선안: `isUploading` 상태일 때 CSS 애니메이션 스피너(예: `border-radius: 50%, border: 2px solid, animation: spin`)를 버튼 내부에 추가.

---

**3. 인라인 편집 힌트 없음 — 셀 편집 가능 여부를 사용자가 알기 어려움**

- 관련 파일: `frontend/src/components/DetailReqTable.tsx` (line 169~179)
- 문제: 편집 가능한 셀(category, name, content)에 편집 가능 힌트가 없음. 커서가 `pointer`로만 변경될 뿐, 사용자가 클릭하면 편집이 가능하다는 시각적 단서(예: 연필 아이콘, `title` tooltip, 셀 hover 배경색 변화)가 없음.
- 설계 명세: ui-design.md "디자인 결정 및 가정 사항" — "인라인 편집 트리거: 셀 단순 클릭 — 발견 가능성을 위해 hint 텍스트 추가" 명시.
- 개선안: 편집 가능 셀의 span에 `title="클릭하여 편집"` 추가 또는 hover 시 배경색(#F1F5F9) 및 연필 아이콘 표시.

---

**4. 에러 배너 닫기 불가 — 잔류 에러가 화면을 가림**

- 관련 파일: `frontend/src/App.tsx` (line 49~64)
- 문제: 에러 배너에 닫기(x) 버튼이 없음. 한번 에러가 발생하면 다음 성공 액션이 있을 때까지 배너가 화면에 잔류함. 특히 잘못된 파일을 선택 후 유효한 파일로 재시도하는 경우에도 에러가 남아있을 수 있음(단, `handleFile`에서 `setError(null)` 처리는 있음).
- 설계 명세: ui-design.md ErrorBanner 컴포넌트 명세의 `onDismiss: () => void — 닫기 핸들러` 속성 명시.
- 개선안: 에러 배너 우측에 `x` 버튼 추가하여 `setError(null)` 호출. `aria-label="오류 닫기"` 적용.

---

**5. 호버/포커스 스타일 미정의 — 키보드 사용자 접근성 저하**

- 관련 파일: `frontend/src/components/OriginalReqTable.tsx` (line 142~158), `frontend/src/components/DownloadBar.tsx` (line 25~58)
- 문제: 생성 버튼, 다운로드 링크에 `:focus-visible` 스타일이 없음. 인라인 스타일로만 구성되어 있어 키보드 탭 이동 시 포커스 표시가 브라우저 기본값에 의존함.
- 설계 명세: ui-design.md 접근성 체크리스트 — "포커스 표시 가시적 — `focus:ring-2 focus:ring-blue-500` 전체 적용" 명시.
- 개선안: 버튼 및 링크 요소에 `onFocus`/`onBlur` 핸들러 또는 CSS 클래스(`focus:outline-2 focus:outline-blue-500`)를 추가하거나, `App.css`에 전역 포커스 스타일 규칙 추가.

---

**6. DownloadBar와 OriginalReqTable에 1단계 다운로드 버튼 중복 렌더링**

- 관련 파일: `frontend/src/components/OriginalReqTable.tsx` (line 122~139), `frontend/src/components/DownloadBar.tsx` (line 25~39)
- 문제: `parsed` phase에서 `DownloadBar`와 `OriginalReqTable` 하단 모두에 "1단계 다운로드" 버튼이 렌더링됨. `DownloadBar`는 `phase !== 'upload'`이면 항상 표시되고, `OriginalReqTable`도 `sessionId`가 있으면 동일 다운로드 링크를 표시함. 사용자에게 동일 기능이 두 번 노출되어 혼란을 줄 수 있음.
- 개선안: `OriginalReqTable` 하단의 1단계 다운로드 링크를 제거하고 `DownloadBar`로 통합하거나, `OriginalReqTable`의 버튼을 `DownloadBar`가 없을 때만 표시하는 조건을 추가.

---

**7. 진행 바의 퍼센트 미표시 — 정보량 부족**

- 관련 파일: `frontend/src/components/DetailReqTable.tsx` (line 191~220)
- 문제: 생성 중 진행 표시 바의 너비가 하드코딩(`width: '60%'`)되어 있으며, 현재 몇 건이 생성되었는지 카운터가 표시되지 않음. SSE 스트리밍으로 행이 추가됨에도 불구하고 진행 정보가 고정 표시됨.
- 설계 명세: ui-design.md ProgressIndicator 명세 — "SSE item 이벤트 수신마다 current 증가. total이 있으면 퍼센트 바, 없으면 스피너 + 카운터" 명시.
- 개선안: 제목 영역에 이미 "상세요구사항 (N건)"이 표시되므로, 진행 바 하단 텍스트에 현재 생성 수를 포함하여 "AI가 상세요구사항을 생성하는 중입니다... (N건 생성됨)" 형식으로 변경.

---

## 스크린샷

소스코드 정적 분석으로 수행되어 스크린샷 캡처는 생략되었습니다.
실제 렌더링 검증이 필요한 경우, 앱 실행 후 Playwright를 활용한 재검수를 권장합니다.

---

## 종합 의견

구현된 UI는 설계 문서(ui-design.md)의 핵심 요소를 충실히 반영하고 있습니다.

- 화면 전환 흐름(upload → parsed → generated)이 `phase` 상태 기반으로 정확히 구현되었습니다.
- 디자인 토큰의 색상값이 설계 문서와 일치하게 적용되었습니다.
- 접근성 기본 항목(`role="alert"`, `aria-label`, `role="log"`, `aria-live`, `tabIndex`, `scope`)이 구현되었습니다.
- 비활성화 조건이 요구사항에 맞게 구현되었습니다.

주요 개선 요점은 **반응형 레이아웃** 미처리(Minor 1)와 **1단계 다운로드 버튼 중복**(Minor 6)입니다. 두 항목 모두 Blocker는 아니나, 실사용 환경에서 UX 혼란을 야기할 수 있어 조기 수정을 권장합니다.
