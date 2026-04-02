# REQ — 개발 환경

> 이 파일은 Developer가 구현 완료 후 **실제 동작하는 명령어**로 업데이트합니다.

## 기술 스택

- **언어**: Python 3.11+ (백엔드) / TypeScript 5.x (프론트엔드)
- **프레임워크**: FastAPI (백엔드) / React 19 + Vite 8 (프론트엔드)
- **상태관리**: Zustand 5 (프론트엔드)
- **HTTP 클라이언트**: Axios 1.x (REST) + fetch ReadableStream (SSE)
- **데이터베이스**: 인메모리 (DB 없음 — 단일 세션 기반)
- **패키지 매니저**: pip (백엔드) / npm (프론트엔드)

## 백엔드 설치

```bash
cd backend

# venv 생성 (최초 1회)
python -m venv .venv

# venv 활성화
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

## 백엔드 실행

```bash
cd backend
python run.py
```

> **Windows 주의**: `claude-agent-sdk`는 `asyncio.ProactorEventLoop`가 필요하다.
> `run.py`는 uvicorn 시작 전에 `WindowsProactorEventLoopPolicy`를 설정하여 이 문제를 해결한다.
> 직접 `uvicorn` 명령어로 실행하면 `SelectorEventLoop`가 사용되어 SDK 호출이 실패한다.

서버 기동 후 헬스 체크:
```bash
curl http://localhost:8000/health
# 응답: {"status": "ok"}
```

## 백엔드 테스트

```bash
cd backend
python -m pytest tests/ -v
```

특정 테스트 모듈만 실행:
```bash
cd backend
python -m pytest tests/test_foundation.py -v
```

## 프론트엔드 설치

```bash
cd frontend
npm install
```

## 프론트엔드 실행

```bash
# 개발 서버 실행 (http://localhost:3000)
cd frontend
npm run dev
```

## 프론트엔드 테스트

```bash
# 단위 테스트 실행 (vitest)
cd frontend
npm run test

# 테스트 감시 모드
cd frontend
npm run test:watch
```

## 빌드

```bash
# 백엔드는 별도 빌드 없이 uvicorn으로 직접 실행

# 프론트엔드 프로덕션 빌드
cd frontend
npm run build
```

## 포트

| 서비스 | 포트 | URL |
|--------|------|-----|
| Frontend (Vite dev) | 3000 | http://localhost:3000 |
| Backend (FastAPI) | 8000 | http://localhost:8000 |

## 환경 변수

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| `ANTHROPIC_API_KEY` | Claude API 인증 키 (`AI_BACKEND=anthropic_api` 시 필수) | 없음 | 조건부 |
| `AI_BACKEND` | AI 백엔드 선택 (`anthropic_api` 또는 `claude_code_sdk`) | `claude_code_sdk` | 아니오 |

`.env` 파일 설정 방법:
```bash
cp backend/.env.example backend/.env
# 에디터로 backend/.env 파일을 열어 필요한 값을 입력
```

### AI_BACKEND 별 사전 조건

| 백엔드 | 조건 |
|--------|------|
| `anthropic_api` | `ANTHROPIC_API_KEY` 환경변수 필수 |
| `claude_code_sdk` (기본값) | `claude-agent-sdk` Python 패키지 설치 + Claude.ai Pro/Max 로그인 유지 |

#### claude-agent-sdk 설치 (claude_code_sdk 사용 시)

```bash
cd backend

# venv 활성화 후 패키지 설치
.venv\Scripts\activate        # Windows
pip install claude-agent-sdk

# 설치 확인
python -c "from claude_agent_sdk import query; print('OK')"
```

Claude.ai 로그인 (최초 1회):
```bash
# npm으로 Claude Code CLI 설치 (claude-agent-sdk가 내부적으로 claude 바이너리를 사용)
npm install -g @anthropic-ai/claude-code

# Claude.ai 로그인
claude
# 대화형 로그인 프로세스를 따라 진행
```

> SEC-006-01: `.env` 파일은 `.gitignore`에 등록되어야 하며 소스 코드에 하드코딩 금지

## 디렉토리 구조 (백엔드)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 앱, CORS 설정
│   ├── state.py         # 인메모리 싱글턴 상태 관리
│   ├── models/
│   │   ├── requirement.py   # OriginalRequirement, DetailRequirement
│   │   ├── session.py       # SessionState, ChatMessage
│   │   └── api.py           # 요청/응답 스키마
│   ├── routers/         # Wave 2~5에서 추가
│   ├── services/        # Wave 2~5에서 추가
│   └── parser/
│       ├── hwp_ole_reader.py   # project-mgmt에서 복사 (수정 금지)
│       └── hwp_body_parser.py  # project-mgmt에서 복사 (수정 금지)
├── data/tmp/            # HWP 임시 파일 저장소 (처리 후 자동 삭제)
├── tests/
│   └── test_foundation.py   # UT-006-02, UT-006-03
├── .env.example
└── requirements.txt
```

## E2E 테스트

### Playwright 설치

```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

### E2E 테스트 실행

```bash
cd frontend
npx playwright test
```

### 테스트용 샘플 파일

| 용도 | 경로 |
|------|------|
| HWP 업로드 테스트 | `frontend/e2e/sample.hwp` |

> `frontend/e2e/sample.hwp`는 git 미추적 파일(`.gitignore`)입니다. 테스트 시 직접 준비하여 해당 경로에 배치하세요.
>
> E2E 테스트 파일은 `frontend/e2e/` 디렉토리에 작성한다.

---

## Gate 관리 명령어

```bash
# 현재 Gate 정합성 검사
python vulcan.py check-trace

# Gate 상태 업데이트
python vulcan.py session --gate gate1 --status done --feature "기능명"

# 스냅샷 생성
python vulcan.py export
```
