# REQ-006 설계 — 시스템 아키텍처 및 비기능 요구사항

> 통합 설계 문서 참조: `req-all-design.md`

## 담당 범위

REQ-006-01 ~ REQ-006-04: FE/BE 분리, 파서 재활용, 보안 정책, 세션 연속성

## 디렉토리 구조

```
extract-req/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI 앱 진입점
│   │   ├── routers/              # API 라우터
│   │   │   ├── upload.py         # POST /api/v1/upload
│   │   │   ├── generate.py       # POST /api/v1/generate (SSE)
│   │   │   ├── chat.py           # POST /api/v1/chat (SSE)
│   │   │   └── download.py       # GET /api/v1/download
│   │   ├── services/
│   │   │   ├── hwp_parse.py      # HwpParseService
│   │   │   ├── ai_generate.py    # AiGenerateService
│   │   │   ├── chat.py           # ChatService
│   │   │   └── excel_export.py   # ExcelExportService
│   │   ├── parser/               # project-mgmt에서 복사 재활용
│   │   │   ├── hwp_ole_reader.py
│   │   │   └── hwp_body_parser.py
│   │   ├── state.py              # SessionStore (인메모리)
│   │   └── models.py             # Pydantic 모델
│   ├── data/tmp/                 # 임시 파일 (자동 삭제)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/           # React 컴포넌트
│   │   ├── store/                # Zustand 상태
│   │   ├── api/                  # API 클라이언트
│   │   └── App.tsx
│   └── package.json
└── docker-compose.yml
```

## 포트 및 통신

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- CORS: localhost:3000 허용

## UT-ID

| UT-ID | 대상 | 검증 내용 |
|-------|------|---------|
| UT-006-01 | CORS 설정 | localhost:3000 요청 허용 확인 |
| UT-006-02 | 파서 재활용 | HWPOLEReader, HwpBodyParser import 성공 |
| UT-006-03 | SessionStore | 세션 저장/조회/삭제 정상 동작 |
| UT-006-04 | 세션 연속성 | 업로드 후 generate, chat, download가 동일 세션 데이터 사용 |

## SEC-ID

| SEC-ID | 내용 |
|--------|------|
| SEC-006-01 | ANTHROPIC_API_KEY 환경변수 관리, .env 파일 .gitignore 등록 |
| SEC-006-02 | CORS allowedOrigins 화이트리스트 제한 |
