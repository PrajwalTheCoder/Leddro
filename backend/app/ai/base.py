import abc
from typing import Dict, Any, Optional

class AIError(Exception):
    """Base exception for all AI provider operations."""
    pass

class AIConfigurationError(AIError):
    """Raised when an AI provider is missing credentials or misconfigured."""
    pass

class AIProviderError(AIError):
    """Raised when an upstream AI service returns an error."""
    pass

class AIRateLimitError(AIError):
    """Raised when an AI provider responds with HTTP 429 rate limit or quota exhausted."""
    pass

class AITimeoutError(AIError):
    """Raised when an AI request times out."""
    pass

class AIResponseParseError(AIError):
    """Raised when an AI provider response cannot be parsed into valid structured JSON."""
    pass

class AIValidationError(AIError):
    """Raised when output fails factual or structure validation."""
    pass

def mask_api_key(key: Optional[str]) -> str:
    """Safely masks an API key so secrets are never displayed or logged."""
    if not key or not key.strip():
        return "Not configured"
    clean = key.strip()
    if len(clean) <= 8:
        return "Configured (***)"
    return f"{clean[:4]}...{clean[-4:]}"

class BaseAIProvider(abc.ABC):
    """Abstract base provider interface for AI-powered email drafting."""
    provider_id: str
    name: str
    is_local: bool = False

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the provider has all required credentials or local endpoints."""
        pass

    @abc.abstractmethod
    def get_status_message(self) -> str:
        """Returns a user-friendly configuration status message."""
        pass

    @abc.abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Tests provider connectivity without generating an email."""
        pass

    @abc.abstractmethod
    async def generate_structured_draft(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Executes a generation request and returns parsed JSON dict matching StructuredDraftOutput.
        """
        pass
