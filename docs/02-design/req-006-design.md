# REQ-006 설계 — 시스템 아키텍처 및 비기능 요구사항

> Gate 2a — 담당 범위: REQ-006-01 ~ REQ-006-04

---

## 디렉토리 구조

```
extract-req/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadPanel.tsx
│   │   │   ├── OriginalReqTable.tsx
│   │   │   ├── DetailReqTable.tsx
│   │   │   ├── InlineEditCell.tsx
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── DownloadBar.tsx
│   │   ├── store/
│   │   │   └── useAppStore.ts     # Zustand 전역 상태
│   │   ├── api/
│   │   │   └── index.ts           # API 클라이언트 + SSE 헬퍼
│   │   ├── types/
│   │   │   └── index.ts           # TypeScript 타입 정의
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI 앱, CORS 설정
│   │   ├── state.py               # 인메모리 싱글턴
│   │   ├── models/
│   │   │   ├── requirement.py     # OriginalRequirement, DetailRequirement
│   │   │   ├── session.py         # SessionState
│   │   │   └── api.py             # 요청/응답 스키마
│   │   ├── routers/
│   │   │   ├── upload.py          # POST /api/v1/upload
│   │   │   ├── generate.py        # POST /api/v1/generate (SSE)
│   │   │   ├── chat.py            # POST /api/v1/chat (SSE)
│   │   │   └── download.py        # GET /api/v1/download
│   │   ├── services/
│   │   │   ├── hwp_parse_service.py
│   │   │   ├── ai_generate_service.py
│   │   │   ├── chat_service.py
│   │   │   └── excel_export_service.py
│   │   └── parser/                # project-mgmt에서 복사 (수정 금지)
│   │       ├── hwp_ole_reader.py
│   │       └── hwp_body_parser.py
│   ├── data/tmp/                  # 임시 파일 저장소 (처리 후 자동 삭제)
│   ├── .env                       # ANTHROPIC_API_KEY (gitignore)
│   └── requirements.txt
│
└── docker-compose.yml
```

---

## 포트 및 통신

| 서비스 | 포트 | 비고 |
|--------|------|------|
| Frontend (Vite dev) | 3000 | `http://localhost:3000` |
| Backend (FastAPI) | 8000 | `http://localhost:8000` |

CORS 설정 (`app/main.py`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 인메모리 상태 관리

### `app/state.py` — 서버 측 싱글턴

```python
from app.models.session import SessionState

_session: SessionState | None = None

def get_session() -> SessionState:
    global _session
    if _session is None:
        _session = SessionState()
    return _session

def reset_session() -> SessionState:
    """새 HWP 업로드 시 호출. 이전 세션 데이터 전체 폐기."""
    global _session
    _session = SessionState()
    return _session
```

### 세션 상태 전이

```
idle
  ↓ POST /api/v1/upload 완료
parsed
  ↓ POST /api/v1/generate 완료
generated
  ↓ POST /api/v1/chat 또는 인라인 편집 (상태 변경 없이 데이터만 갱신)
generated
  ↓ GET /api/v1/download
done  (다운로드 후에도 상태 유지, 추가 수정 가능)
```

### 세션 초기화 조건

| 트리거 | 동작 |
|--------|------|
| 새 HWP 파일 업로드 | `reset_session()` 호출 후 파싱 시작 |
| 서버 재시작 | 전역 변수 소멸 → 자동 초기화 |

### `app/models/session.py`

```python
class SessionState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["idle", "parsed", "generated", "done"] = "idle"
    original_requirements: list[OriginalRequirement] = []
    detail_requirements: list[DetailRequirement] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## API 클라이언트 (`src/api/index.ts`)

```typescript
// SSE는 POST 바디 전달이 필요하므로 EventSource(GET 전용) 대신
// fetch + ReadableStream 사용
function generateDetailStream(
  sessionId: string,
  callbacks: { onItem, onDone, onError }
): () => void  // cleanup 함수 반환

function chatStream(
  req: ChatRequest,
  callbacks: { onText, onPatch, onDone, onError }
): () => void
```

---

## 환경 설정

### `backend/.env`

```
ANTHROPIC_API_KEY=sk-ant-...
```

`.gitignore`에 `.env` 반드시 포함.

### `backend/requirements.txt`

```
fastapi
uvicorn[standard]
python-multipart
anthropic
openpyxl
olefile
pydantic>=2.0
```

### `frontend/package.json` 주요 의존성

```json
{
  "dependencies": {
    "react": "^18",
    "zustand": "^4",
    "axios": "^1"
  },
  "devDependencies": {
    "vite": "^5",
    "@vitejs/plugin-react": "^4",
    "typescript": "^5"
  }
}
```

---

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-006-01 | CORS | `localhost:3000` → 200, `localhost:9999` → 403 |
| UT-006-02 | 파서 재활용 | `HWPOLEReader`, `HwpBodyParser` import 성공, 수정 없음 확인 |
| UT-006-03 | `SessionStore` | 저장/조회/reset 정상 동작 |
| UT-006-04 | 세션 연속성 | upload → generate → chat → download가 동일 session_id 사용 |

---

## SEC-ID

| SEC-ID | 내용 |
|--------|------|
| SEC-006-01 | `ANTHROPIC_API_KEY` `.env` 관리, `.gitignore` 등록 확인 |
| SEC-006-02 | CORS `allow_origins` 화이트리스트 제한 (와일드카드 `*` 금지) |
