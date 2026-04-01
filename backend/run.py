"""uvicorn 시작 래퍼.

Windows에서 asyncio.create_subprocess_exec (claude-agent-sdk 필요)를 사용하려면
ProactorEventLoop가 필요하다. uvicorn은 worker 프로세스 생성 전에 이벤트 루프를
초기화하므로, main.py에서 policy를 바꾸면 너무 늦다.
이 파일을 통해 시작하면 uvicorn이 이벤트 루프를 생성하기 전에 policy가 설정된다.
"""

import sys

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
