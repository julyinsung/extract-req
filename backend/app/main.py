"""FastAPI 애플리케이션 진입점.

CORS는 SEC-006-02에 따라 와일드카드 '*' 없이 localhost:3000만 허용한다.
SEC-002-01: .env 파일에서 환경변수를 로드하여 ANTHROPIC_API_KEY를 주입한다.
REQ-013: lifespan startup 시 snapshot.load_snapshot()으로 인메모리 state를 복원한다.
"""

import logging
import sys
from contextlib import asynccontextmanager

# Windows에서 asyncio.create_subprocess_exec 지원을 위해 ProactorEventLoop를 사전 설정한다.
# SelectorEventLoop(uvicorn --reload 기본값)는 subprocess를 지원하지 않아
# claude-agent-sdk의 CLIConnectionError(NotImplementedError)가 발생한다.
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.snapshot as snapshot
from app.routers import chat, detail, download, generate, upload

logger = logging.getLogger(__name__)

# 서버 기동 시 .env에서 환경변수를 로드한다 — API 키 하드코딩 방지
load_dotenv()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """서버 기동/종료 생명주기 관리 (REQ-013).

    startup: 스냅샷 파일이 존재하면 인메모리 state를 복원한다.
    복원 실패 시 서버 기동을 중단하지 않고 빈 state로 정상 기동한다.
    shutdown: 변경 시마다 저장이 완료되므로 별도 처리 없음.
    """
    restored = snapshot.load_snapshot()
    if restored:
        logger.info("서버 기동: 스냅샷 복원 성공")
    else:
        logger.info("서버 기동: 스냅샷 없음 또는 복원 실패 — 빈 state로 기동")
    yield
    # shutdown: 파일은 변경 시마다 저장되므로 별도 처리 없음


app = FastAPI(title="Extract REQ API", lifespan=lifespan)

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
