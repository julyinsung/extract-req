# REQ-010 / REQ-011 / REQ-012 설계 문서

## 개요

- **REQ 그룹**: REQ-010 — 생성 진행률 표시, REQ-011 — 채팅창 Sticky 고정, REQ-012 — 상세요구사항 행 삭제
- **설계 방식**: 기존 Layered 아키텍처(FastAPI + Zustand) 위에 최소 변경 원칙으로 기능을 추가한다
- **핵심 결정사항**: 세 요구사항 모두 신규 추상화 계층 없이 기존 모듈을 점진적으로 확장하는 방식으로 구현한다. REQ-010은 SSE 스트림에 이벤트 타입 추가, REQ-011은 CSS 레이아웃 속성 변경, REQ-012는 신규 라우터 엔드포인트 + 스토어 액션 추가로 완결된다.

---

## 시스템 구조

```
REQ-010 (진행률)
  generate.py (router)
    └─ ai_generate_service.py / ai_generate_service_sdk.py
         └─ _parse_obj() 호출 후 progress SSE 이벤트 yield
  ←SSE→
  useAppStore.ts
    └─ progress 상태 (progressCurrent, progressTotal, progressReqId) 추가
  DetailReqTable.tsx
    └─ 진행률 UI: "N / M 항목 생성 중 (REQ-NNN)" 텍스트 + 진행률 바

REQ-011 (Sticky 채팅창)
  App.tsx
    └─ #chat-area div: position 속성 변경 (flex child → sticky)
  ChatPanel.tsx
    └─ 높이 자동 계산 또는 max-height 제약 추가

REQ-012 (행 삭제)
  detail.py (router) ← DELETE /api/v1/detail/{id} 엔드포인트 추가
  state.py ← delete_detail(req_id) 함수 추가
  api.ts (frontend) ← deleteDetailReq(id) 함수 추가
  useAppStore.ts ← deleteDetailReq 액션 추가
  DetailReqTable.tsx ← 삭제 버튼 + 확인 다이얼로그 추가
```

---

## 모듈/컴포넌트 설계

### REQ-010: 생성 진행률 표시

#### 백엔드 — `ai_generate_service.py` / `ai_generate_service_sdk.py`

- **책임**: 각 원본 요구사항 그룹 처리 직후 `progress` SSE 이벤트를 yield한다
- **변경 위치**: `generate_stream()` 메서드 내부, `_parse_obj()`가 `item` 이벤트를 반환한 직후
- **이벤트 형식**:
  ```
  data: {"type": "progress", "current": N, "total": M, "req_id": "REQ-NNN"}
  ```
  - `current`: 지금까지 처리 완료된 원본 요구사항 수 (1-based)
  - `total`: 전체 원본 요구사항 수 (`len(originals)`)
  - `req_id`: 방금 처리한 원본 요구사항의 `id`
- **제약**: `total`은 스트리밍 시작 전 `originals` 목록 길이로 확정된다. parent_id 기준으로 그룹이 완료(해당 parent의 마지막 item이 yield된 시점)될 때 한 번만 발행한다.
- **결정 근거**: item 이벤트마다 progress를 발행하면 동일 parent의 항목이 여럿 생성될 때 N이 과다 증가한다. parent_id 그룹 완료 단위로 발행하여 "원본 요구사항 N번째 완료" 의미를 정확히 전달한다.
- **두 서비스 파일 모두 수정**: `ai_generate_service.py`와 `ai_generate_service_sdk.py`는 동일한 SSE 인터페이스를 준수하므로 동일한 progress 로직을 각각 추가한다.

#### 프론트엔드 — `useAppStore.ts`

- **책임**: `progress` 이벤트 수신 시 진행 상태를 저장한다
- **추가 상태 필드**:
  ```typescript
  progressCurrent: number      // 기본값 0
  progressTotal: number        // 기본값 0
  progressReqId: string | null // 기본값 null
  ```
- **추가 액션**:
  ```typescript
  setProgress(current: number, total: number, reqId: string): void
  clearProgress(): void
  ```
- **제약**: `isGenerating`이 false가 될 때 `clearProgress()`를 함께 호출하여 완료 후 진행률이 잔존하지 않도록 한다. 두 상태를 별도 액션으로 분리하는 이유는 `done` 이벤트 수신 시점과 `isGenerating` 해제 시점이 다를 수 있기 때문이다.

#### 프론트엔드 — SSE 수신 로직 (generate 호출 측)

- **책임**: `progress` 이벤트 파싱 및 스토어 갱신
- **변경 위치**: `UploadPanel.tsx` 또는 generate SSE 처리 콜백 — `event.data`의 `type === 'progress'`를 감지하여 `setProgress()` 호출
- **제약**: 기존 `item`, `done`, `error` 이벤트 처리 흐름을 변경하지 않는다

#### 프론트엔드 — `DetailReqTable.tsx`

- **책임**: 진행률 상태를 시각적으로 표시하고, 완료 후 자동 제거한다
- **인터페이스**: `useAppStore`에서 `progressCurrent`, `progressTotal`, `progressReqId`를 구독
- **표시 조건**: `isGenerating && progressTotal > 0`
- **표시 내용**: `"N / M 항목 생성 중 (REQ-NNN)"` 텍스트와 `progressCurrent / progressTotal` 비율의 진행률 바
- **제거 조건**: `isGenerating === false` 시 진행률 UI 비표시 — 이미 존재하는 `{isGenerating && ...}` 조건 블록 내에 위치시키면 별도 제거 로직 불필요
- **결정 근거**: 기존 DetailReqTable에 이미 `isGenerating` 기반 pulse 바가 있다. 이를 실제 진행률 바로 교체하는 방식으로 변경 최소화

---

### REQ-011: 채팅창 Sticky 고정

#### 현재 레이아웃 구조 분석

`App.tsx` 기준:
- 최상위 div: `padding: 24px 32px`, 일반 흐름 (`position: static`)
- `#table-area`: `flex: 1, minWidth: 0` — 좌측 콘텐츠 영역
- `#chat-area`: `width: 380, flexShrink: 0` — 우측 채팅 패널 (현재 `flex-start` 정렬)
- `ChatPanel` 내부 height: 고정 600px

현재 문제: `#chat-area`가 일반 flex 자식이므로 페이지 스크롤 시 뷰포트 밖으로 사라진다.

#### 설계 방향: `position: sticky` 적용

**변경 대상**: `App.tsx`의 `#chat-area` div

- `position: sticky`
- `top: 24px` — 헤더 아래 여백 유지
- `alignSelf: flex-start` — 이미 적용됨, 유지
- `maxHeight: calc(100vh - 48px)` — 뷰포트 높이 초과 방지
- `overflowY: auto` — 채팅 내역이 많을 경우 내부 스크롤

**`ChatPanel.tsx` 변경**:
- 고정 height 600px 제거 → `height: 100%` 또는 최소 높이(`minHeight`)로 대체
- 대화 내역 영역(`role="log"`)의 `flex: 1` 유지 — 내부 스크롤은 해당 영역에서 처리

**제약**:
- sticky는 스크롤 컨테이너(부모 중 overflow가 hidden/scroll인 요소)가 있으면 동작하지 않는다. 현재 최상위 div는 overflow 미지정이므로 sticky가 정상 동작할 것으로 예상되나, Developer가 실제 렌더링에서 동작 여부를 검증해야 한다.
- `#table-area`는 `overflow: visible`을 유지해야 sticky가 뷰포트 기준으로 작동한다.
- 테이블 영역 스크롤 방해 금지(AC-011-03): `#chat-area`의 너비가 flex 레이아웃으로 우측에 고정되므로 좌측 테이블 콘텐츠를 가리지 않는다. 단, 모바일 뷰포트에서 chat-area가 table-area와 겹칠 경우 별도 처리가 필요하지만, 현재 요구사항은 데스크톱 환경만 대상으로 한다(REQUIREMENTS.md 범위 참조).
- **결정 근거**: `position: fixed`는 뷰포트 기준 절대 위치라 flex 레이아웃에서 공간을 차지하지 않아 테이블이 전체 너비를 점유하게 된다. `sticky`는 일반 흐름을 유지하면서 스크롤 시 고정되므로 레이아웃 변경을 최소화한다.

---

### REQ-012: 상세요구사항 행 삭제

#### 백엔드 — `state.py`

- **추가 함수**:
  ```python
  def delete_detail(req_id: str) -> bool
  ```
- **책임**: 해당 id의 `DetailRequirement`를 `session.detail_requirements` 목록에서 제거한다
- **반환**: 삭제 성공 시 `True`, 해당 id 없으면 `False`
- **제약**: 기존 `_lock` 패턴을 동일하게 사용하여 스레드 안전성을 보장한다

#### 백엔드 — `detail.py` (router)

- **추가 엔드포인트**:
  ```
  DELETE /api/v1/detail/{id}
  ```
- **인터페이스**:
  - 경로 파라미터: `id: str`
  - 성공 응답 200: `{"deleted_id": "<id>"}`
  - 404: `ErrorResponse(code="NOT_FOUND", message="...")`
- **처리 흐름**: `state.delete_detail(id)` 호출 → `False`이면 404 raise → 성공이면 `{"deleted_id": id}` 반환
- **제약**: 요청 바디 없음. id는 경로 파라미터만으로 식별한다. `ErrorResponse` 모델은 기존 `app.models.api`의 것을 그대로 사용한다.
- **결정 근거**: PATCH와 동일 라우터 파일(`detail.py`)에 배치하여 상세요구사항 CRUD를 한 파일에서 관리한다.

#### 프론트엔드 — `api.ts` (또는 API 함수 파일)

- **추가 함수**:
  ```typescript
  deleteDetailReq(id: string): Promise<{ deleted_id: string }>
  ```
- **동작**: `DELETE /api/v1/detail/{id}` 호출. 404 수신 시 Error를 throw한다.

#### 프론트엔드 — `useAppStore.ts`

- **추가 액션**:
  ```typescript
  deleteDetailReq(id: string): Promise<void>
  ```
- **책임**: `deleteDetailReq` API 호출 → 성공 시 스토어에서 해당 id 제거 → 실패 시 `error` 상태 설정
- **낙관적 업데이트 사용 안 함**: `syncPatchDetailReq`와 동일한 서버 확인 후 스토어 갱신 정책을 적용한다. 삭제는 되돌릴 수 없는 작업이므로 서버 응답 확인 후 UI 반영이 안전하다.
- **스토어 상태 제거 방법**: `detailReqs.filter(r => r.id !== id)`

#### 프론트엔드 — `DetailReqTable.tsx`

- **삭제 버튼 추가**: 각 행(tr)에 삭제 버튼 열(td) 추가
- **확인 다이얼로그**: 브라우저 기본 `window.confirm()` 사용 — "이 항목을 삭제하시겠습니까?" 메시지. 취소 시 아무 동작 없음.
- **비활성화 조건**: `isGenerating` 중에는 삭제 버튼 비활성화 — 생성 중 삭제로 인한 index 오염 방지
- **테이블 헤더 변경**: 삭제 버튼 열을 위한 헤더 컬럼 추가 (예: 빈 헤더 또는 "삭제")
- **결정 근거**: `window.confirm()`은 외부 라이브러리 없이 확인 다이얼로그(AC-012-03)를 구현하는 가장 단순한 방법이다. 현재 프로젝트 규모에서 추가 modal 컴포넌트 도입은 오버엔지니어링이다.

---

## API 설계

| Method | Path | 설명 | 인증 | 요청 | 응답 |
|--------|------|------|------|------|------|
| DELETE | `/api/v1/detail/{id}` | 특정 상세요구사항 삭제 | 없음 | 경로 파라미터만 | `{"deleted_id": "<id>"}` |

### SSE 이벤트 추가 (REQ-010)

기존 `POST /api/v1/generate` SSE 스트림에 새 이벤트 타입 추가:

```
data: {"type": "progress", "current": N, "total": M, "req_id": "REQ-NNN"}
```

전체 SSE 이벤트 시퀀스 (변경 후):

```
data: {"type": "item", "data": {...}}         ← 기존
data: {"type": "progress", "current": 1, "total": 5, "req_id": "REQ-001"}  ← 신규
data: {"type": "item", "data": {...}}
data: {"type": "item", "data": {...}}
data: {"type": "progress", "current": 2, "total": 5, "req_id": "REQ-002"}  ← 신규
...
data: {"type": "done", "total": 12}           ← 기존
```

### 에러 응답

| HTTP | 코드 | 상황 |
|------|------|------|
| 404 | `NOT_FOUND` | 삭제 대상 id가 존재하지 않음 |

---

## 디렉토리 구조 — 변경 대상 파일

```
backend/
└── app/
    ├── state.py                        ← delete_detail() 함수 추가
    ├── routers/
    │   └── detail.py                   ← DELETE /api/v1/detail/{id} 엔드포인트 추가
    └── services/
        ├── ai_generate_service.py      ← generate_stream()에 progress 이벤트 추가
        └── ai_generate_service_sdk.py  ← generate_stream()에 progress 이벤트 추가

frontend/src/
├── api.ts (또는 api/ 디렉토리)         ← deleteDetailReq() 함수 추가
├── store/
│   └── useAppStore.ts                  ← progress 상태 + deleteDetailReq 액션 추가
├── components/
│   ├── DetailReqTable.tsx              ← 삭제 버튼 + 진행률 UI 교체
│   └── ChatPanel.tsx                   ← 고정 height 제거
└── App.tsx                             ← #chat-area sticky 속성 추가
```

**불변 파일** (수정 불필요):
- `backend/app/models/api.py` — `ErrorResponse` 재사용, 신규 모델 불필요
- `backend/app/routers/generate.py` — 라우터 레이어 변경 없음, 서비스 레이어에서만 처리
- `backend/app/models/requirement.py` — `DetailRequirement` 모델 변경 없음
- `frontend/src/components/OriginalReqTable.tsx` — 영향 없음
- `frontend/src/components/UploadPanel.tsx` — generate SSE 처리 콜백에 progress 처리 추가 필요시 수정. 현재 generate 호출 위치를 Developer가 확인 후 결정

---

## 단위 테스트 ID 사전 할당

| UT-ID | 대상 | 설명 | REQ-ID |
|-------|------|------|--------|
| UT-010-01 | `AiGenerateService.generate_stream()` | item 이벤트 직후 progress 이벤트가 발행되는지 확인 (current 1, total N) | REQ-010-01 |
| UT-010-02 | `AIGenerateServiceSDK.generate_stream()` | SDK 서비스도 동일한 progress 이벤트를 발행하는지 확인 | REQ-010-01 |
| UT-010-03 | `AiGenerateService.generate_stream()` | progress.current 값이 parent_id 완료 순서(1-based)와 일치하는지 확인 | REQ-010-01 |
| UT-010-04 | `DetailReqTable` | `isGenerating=true`, `progressTotal>0` 시 진행률 텍스트 "N / M 항목 생성 중" 렌더링 | REQ-010-02 |
| UT-010-05 | `DetailReqTable` | `isGenerating=false` 시 진행률 UI가 DOM에서 사라지는지 확인 | REQ-010-03 |
| UT-011-01 | `App` 레이아웃 | `#chat-area`에 `position: sticky` 스타일이 적용되어 있는지 확인 | REQ-011-01 |
| UT-011-02 | `ChatPanel` | sticky 상태에서 채팅 전송 버튼 클릭 → `handleSend` 호출되는지 확인 (기능 정상 동작) | REQ-011-02 |
| UT-012-01 | `state.delete_detail()` | 존재하는 id 삭제 시 True 반환 및 목록에서 제거 | REQ-012-02 |
| UT-012-02 | `state.delete_detail()` | 존재하지 않는 id 삭제 시 False 반환 | REQ-012-02 |
| UT-012-03 | `DELETE /api/v1/detail/{id}` | 존재하는 id 요청 시 200 + `{"deleted_id": id}` 반환 | REQ-012-02 |
| UT-012-04 | `DELETE /api/v1/detail/{id}` | 존재하지 않는 id 요청 시 404 반환 | REQ-012-02 |
| UT-012-05 | `DetailReqTable` | 삭제 버튼 클릭 → confirm 다이얼로그 표시 → 취소 시 행 유지 | REQ-012-03 |
| UT-012-06 | `DetailReqTable` | 삭제 버튼 클릭 → confirm 확인 시 해당 행 제거 | REQ-012-01 |
| UT-012-07 | `useAppStore.deleteDetailReq()` | API 성공 시 스토어에서 해당 id 제거 확인 | REQ-012-01 |
| UT-012-08 | `useAppStore.deleteDetailReq()` | API 404 실패 시 스토어 상태 불변 + error 설정 | REQ-012-02 |
| UT-012-09 | `DetailReqTable` | `isGenerating=true` 중 삭제 버튼 비활성화 확인 | REQ-012-01 |

---

## 보안 고려사항

| SEC-ID | 위협 | 대응 방안 | OWASP |
|--------|------|----------|-------|
| SEC-010-01 | progress 이벤트에 민감한 내부 정보 포함 | `req_id`, `current`, `total`만 포함. 원본 요구사항 content는 포함하지 않는다 | A01 |
| SEC-012-01 | 임의 id를 DELETE 요청으로 전달하여 타 항목 삭제 | 현재 단일 사용자 전제(REQ-006-04)이므로 인증 미적용. 다중 사용자 전환 시 세션 기반 소유권 검증 필요 | A01 |
| SEC-012-02 | DELETE id 파라미터에 경로 순회 문자 삽입 | FastAPI 경로 파라미터는 자동 URL 디코딩되나, `state.delete_detail()`에서 id를 문자열 동등 비교만 사용하므로 경로 순회 위협 없음 | A03 |
| SEC-012-03 | 대량 DELETE 요청으로 서버 상태 고갈 | 단일 사용자 전제 + 인메모리 리스트 조작으로 서버 부하 미미. 요청 속도 제한은 현재 요구사항 범위 외 | A05 |
