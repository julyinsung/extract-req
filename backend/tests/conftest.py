"""pytest conftest — claude_agent_sdk 모듈 stub 주입.

claude_agent_sdk가 설치되지 않은 테스트 환경에서도 SDK 서비스 모듈을
import할 수 있도록 sys.modules에 stub을 미리 등록한다.
실제 SDK 동작은 각 테스트에서 patch()로 대체한다.
"""

import sys
import types
from unittest.mock import MagicMock


def _build_claude_agent_sdk_stub() -> types.ModuleType:
    """claude_agent_sdk 패키지의 최소 stub 모듈을 생성한다."""
    stub = types.ModuleType("claude_agent_sdk")

    # 데이터 클래스 stub — isinstance() 체크가 동작하도록 실제 클래스로 정의
    class TextBlock:
        def __init__(self, text: str = ""):
            self.text = text

    class AssistantMessage:
        def __init__(self, content=None):
            self.content = content or []

    class ResultMessage:
        def __init__(self, result: str = "", session_id=None, total_cost_usd=None):
            self.result = result
            self.session_id = session_id
            self.total_cost_usd = total_cost_usd

    class ClaudeAgentOptions:
        def __init__(self, allowed_tools=None, permission_mode="default", cli_path=None, resume=None):
            self.allowed_tools = allowed_tools or []
            self.permission_mode = permission_mode
            self.cli_path = cli_path
            self.resume = resume

    async def query(prompt, options=None):
        """stub — 테스트에서 patch()로 교체된다."""
        return
        yield  # AsyncGenerator 시그니처 유지

    stub.TextBlock = TextBlock
    stub.AssistantMessage = AssistantMessage
    stub.ResultMessage = ResultMessage
    stub.ClaudeAgentOptions = ClaudeAgentOptions
    stub.query = query

    return stub


# 세션 전체에 걸쳐 한 번만 주입한다
if "claude_agent_sdk" not in sys.modules:
    sys.modules["claude_agent_sdk"] = _build_claude_agent_sdk_stub()
