"""FastAPI 애플리케이션 진입점.

CORS는 SEC-006-02에 따라 와일드카드 '*' 없이 localhost:3000만 허용한다.
SEC-002-01: .env 파일에서 환경변수를 로드하여 ANTHROPIC_API_KEY를 주입한다.
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, download, generate, upload

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


@app.get("/health")
def health():
    """서버 기동 상태 확인 엔드포인트."""
    return {"status": "ok"}
