"""AI 백엔드 팩토리 모듈 (REQ-007).

AI_BACKEND 환경변수를 읽어 적절한 서비스 구현체를 반환한다.
라우터가 구체 클래스를 직접 import하지 않도록 의존성 역전을 제공한다.

SEC-007-01: 인식 불가 값은 기본값으로 폴백하고 서버 로그에만 기록한다.
SEC-007-03: 백엔드 유형은 클라이언트 응답에 포함하지 않는다.
"""

import logging
import os

logger = logging.getLogger(__name__)

# 지원 백엔드 목록
_BACKEND_ANTHROPIC_API = "anthropic_api"
_BACKEND_CLAUDE_CODE_SDK = "claude_code_sdk"
_VALID_BACKENDS = {_BACKEND_ANTHROPIC_API, _BACKEND_CLAUDE_CODE_SDK}
_DEFAULT_BACKEND = _BACKEND_CLAUDE_CODE_SDK


def _get_backend() -> str:
    """AI_BACKEND 환경변수를 읽어 유효한 백엔드 이름을 반환한다.

    미설정이면 기본값을, 알 수 없는 값이면 기본값으로 폴백하고 경고 로그를 남긴다.
    """
    value = os.environ.get("AI_BACKEND", _DEFAULT_BACKEND).strip()
    if value not in _VALID_BACKENDS:
        logger.warning(
            "AI_BACKEND 환경변수 값 '%s'는 지원하지 않습니다. "
            "'%s'로 폴백합니다. (지원값: %s)",
            value,
            _DEFAULT_BACKEND,
            ", ".join(sorted(_VALID_BACKENDS)),
        )
        return _DEFAULT_BACKEND
    return value


def get_ai_generate_service():
    """AI_BACKEND 환경변수에 따라 상세요구사항 생성 서비스 인스턴스를 반환한다.

    Returns:
        anthropic_api  → AiGenerateService
        claude_code_sdk (기본값) → AIGenerateServiceSDK
    """
    backend = _get_backend()
    if backend == _BACKEND_ANTHROPIC_API:
        from app.services.ai_generate_service import AiGenerateService
        return AiGenerateService()

    # claude_code_sdk 경로 — ImportError는 호출자(라우터)가 503으로 변환한다
    from app.services.ai_generate_service_sdk import AIGenerateServiceSDK
    return AIGenerateServiceSDK()


def get_chat_service():
    """AI_BACKEND 환경변수에 따라 채팅 서비스 인스턴스를 반환한다.

    Returns:
        anthropic_api  → ChatService
        claude_code_sdk (기본값) → ChatServiceSDK
    """
    backend = _get_backend()
    if backend == _BACKEND_ANTHROPIC_API:
        from app.services.chat_service import ChatService
        return ChatService()

    # claude_code_sdk 경로 — ImportError는 호출자(라우터)가 503으로 변환한다
    from app.services.chat_service_sdk import ChatServiceSDK
    return ChatServiceSDK()
