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
pip install -r requirements.txt
```

## 백엔드 실행

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

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
| `ANTHROPIC_API_KEY` | Claude API 인증 키 | 없음 | 예 |

`.env` 파일 설정 방법:
```bash
cp backend/.env.example backend/.env
# 에디터로 backend/.env 파일을 열어 ANTHROPIC_API_KEY 값을 입력
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

## Gate 관리 명령어

```bash
# 현재 Gate 정합성 검사
python vulcan.py check-trace

# Gate 상태 업데이트
python vulcan.py session --gate gate1 --status done --feature "기능명"

# 스냅샷 생성
python vulcan.py export
```
