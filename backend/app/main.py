"""FastAPI 애플리케이션 진입점.

CORS는 SEC-006-02에 따라 와일드카드 '*' 없이 localhost:3000만 허용한다.
SEC-002-01: .env 파일에서 환경변수를 로드하여 ANTHROPIC_API_KEY를 주입한다.
"""

import sys

# Windows에서 asyncio.create_subprocess_exec 지원을 위해 ProactorEventLoop를 사전 설정한다.
# SelectorEventLoop(uvicorn --reload 기본값)는 subprocess를 지원하지 않아
# claude-agent-sdk의 CLIConnectionError(NotImplementedError)가 발생한다.
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, detail, download, generate, upload

# 서버 기동 시 .env에서 환경변수를 로드한다 — API 키 하드코딩 방지
load_dotenv()

app = FastAPI(title="Extract REQ API")

# SEC-006-02: allow_origins를 화이트리스트로 제한 — 와일드카드 '*' 금지
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(chat.router)
app.include_router(download.router)
app.include_router(detail.router)


@app.get("/health")
def health():
    """서버 기동 상태 확인 엔드포인트."""
    return {"status": "ok"}
