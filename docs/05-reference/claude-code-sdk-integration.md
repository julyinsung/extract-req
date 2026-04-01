# Claude Code SDK 연동 참고 문서

> REQ-007 구현 시 참조 — Claude Code SDK로 AI 백엔드 교체 방법

---

## 개요

현재 구현(Anthropic API)을 유지하면서, Claude Code SDK를 대체 백엔드로 추가한다.
Claude Code CLI는 Claude.ai Pro/Max 구독 자격증명을 사용하므로 API 키가 불필요하다.

---

## 인증 방식 비교

| 항목 | Anthropic API (현재) | Claude Code SDK (신규) |
|------|---------------------|----------------------|
| 인증 | `ANTHROPIC_API_KEY` | Claude.ai 구독 OAuth (`~/.claude/.credentials.json`) |
| 비용 | API 사용량 과금 | Pro/Max 구독 포함 |
| 서버 배포 | `.env` 파일만으로 충분 | Claude Code 설치 + 로그인 유지 필요 |
| 속도 | 빠름 | 프로세스 시작 오버헤드 있음 |
| 동시 요청 | 자연스러운 병렬 처리 | subprocess spawning 비용 |

---

## 설치

```bash
pip install claude-agent-sdk
# 또는 CLI만 사용 시 claude 바이너리가 PATH에 있어야 함
```

---

## 구현 전략

### 설정 방식 (환경변수)

```bash
# .env
AI_BACKEND=anthropic_api      # 기본값
# AI_BACKEND=claude_code_sdk  # Claude Code 사용 시
```

### 서비스 팩토리 패턴

```python
# app/services/ai_backend_factory.py

import os
from app.services.ai_generate_service import AIGenerateService
from app.services.ai_generate_service_sdk import AIGenerateServiceSDK

def get_ai_generate_service():
    backend = os.environ.get("AI_BACKEND", "anthropic_api")
    if backend == "claude_code_sdk":
        return AIGenerateServiceSDK()
    return AIGenerateService()
```

---

## Claude Code SDK 사용법

### 방식 A: CLI subprocess (가장 간단)

```python
import subprocess, json, asyncio
from typing import AsyncGenerator

async def generate_stream_via_cli(prompt: str) -> AsyncGenerator[str, None]:
    """claude -p 명령을 subprocess로 실행하여 스트리밍 응답을 반환한다."""
    
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--allowedTools", "computer"  # 도구 사용 불필요 시 빈 값
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    async for line in process.stdout:
        line = line.decode().strip()
        if not line:
            continue
        event = json.loads(line)
        
        # 텍스트 델타 (실시간 토큰)
        if event.get("type") == "stream_event":
            delta = event.get("event", {}).get("delta", {})
            if delta.get("type") == "text_delta":
                yield delta.get("text", "")
        
        # 최종 결과
        elif event.get("type") == "message":
            if event.get("result"):
                yield event["result"]
    
    await process.wait()
```

### 방식 B: Agent SDK (권장)

```python
from claude_agent_sdk import query, ClaudeAgentOptions
from typing import AsyncGenerator

async def generate_stream_via_sdk(prompt: str) -> AsyncGenerator[str, None]:
    """claude-agent-sdk를 사용하여 스트리밍 응답을 반환한다."""
    
    options = ClaudeAgentOptions(
        allowed_tools=[],  # 요구사항 생성은 도구 불필요
        permission_mode="default",
    )
    
    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "content"):
            yield message.content
        elif hasattr(message, "result"):
            yield message.result
```

---

## ai_generate_service_sdk.py 구현 가이드

`backend/app/services/ai_generate_service.py`를 참고하여 동일한 인터페이스로 구현한다.

```python
# backend/app/services/ai_generate_service_sdk.py

import asyncio, json, re
from typing import AsyncGenerator
from app.state import get_original, set_detail
from app.models.requirement import DetailRequirement

SYSTEM_PROMPT = """..."""  # ai_generate_service.py의 SYSTEM_PROMPT 재사용

class AIGenerateServiceSDK:
    """Claude Code CLI를 백엔드로 사용하는 상세요구사항 생성 서비스."""
    
    async def generate_stream(self, session_id: str) -> AsyncGenerator[str, None]:
        """ai_generate_service.AIGenerateService.generate_stream()과 동일한 SSE 인터페이스."""
        
        originals = get_original(session_id)
        if not originals:
            yield _sse({"type": "error", "message": "파싱된 요구사항이 없습니다."})
            return
        
        # 프롬프트 구성 (기존 서비스와 동일)
        user_prompt = _build_prompt(originals)
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
        
        # Claude Code CLI 호출
        buffer = ""
        details = []
        
        async for chunk in _cli_stream(full_prompt):
            buffer += chunk
            # 기존 _find_obj_end() 로직 재사용하여 JSON 파싱
            # ...
        
        set_detail(session_id, details)
        yield _sse({"type": "done", "total": len(details)})


async def _cli_stream(prompt: str) -> AsyncGenerator[str, None]:
    """claude CLI subprocess 스트리밍."""
    process = await asyncio.create_subprocess_exec(
        "claude", "-p", prompt,
        "--output-format", "stream-json",
        "--verbose", "--include-partial-messages",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    async for line in process.stdout:
        decoded = line.decode().strip()
        if not decoded:
            continue
        try:
            event = json.loads(decoded)
            if event.get("type") == "stream_event":
                delta = event.get("event", {}).get("delta", {})
                if delta.get("type") == "text_delta":
                    yield delta.get("text", "")
        except json.JSONDecodeError:
            pass
    
    await process.wait()
```

---

## chat_service_sdk.py 구현 가이드

```python
# backend/app/services/chat_service_sdk.py
# chat_service.py와 동일한 인터페이스, _cli_stream() 사용

class ChatServiceSDK:
    async def chat_stream(self, session_id: str, user_message: str) -> AsyncGenerator[str, None]:
        """chat_service.ChatService.chat_stream()과 동일한 SSE 인터페이스."""
        # PATCH 태그 프로토콜은 그대로 유지
        # Claude Code CLI로 전체 응답 수집 후 PATCH 추출
        ...
```

---

## 주의사항

1. **서버 환경**: `claude` 바이너리가 PATH에 있어야 함 (`which claude` 로 확인)
2. **인증 유지**: `~/.claude/.credentials.json` — Claude.ai 로그인 세션이 만료되면 재로그인 필요
3. **동시 요청**: subprocess가 여러 개 동시에 실행될 수 있으므로 요청 수 제한 권장
4. **타임아웃**: 긴 응답의 경우 subprocess 타임아웃 설정 필요
5. **Windows**: `asyncio.create_subprocess_exec` 대신 `asyncio.create_subprocess_shell` 필요할 수 있음

---

## 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/app/services/ai_generate_service.py` | 현재 Anthropic API 구현 (참고) |
| `backend/app/services/chat_service.py` | 현재 채팅 서비스 (참고) |
| `backend/app/state.py` | 세션 상태 (재사용) |
| `backend/app/models/requirement.py` | 데이터 모델 (재사용) |
| `docs/02-design/req-004-design.md` | AI 생성 설계 문서 |
| `docs/02-design/req-006-design.md` | 채팅 설계 문서 |

---

## 참고 링크

- Claude Code SDK 공식 문서: Claude Code CLI `--help`
- Agent SDK: `pip show claude-agent-sdk`
- 인증: `~/.claude/settings.json`
