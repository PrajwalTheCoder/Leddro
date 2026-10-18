import time
import json
import httpx
from typing import Dict, Any
from backend.app.ai.base import (
    BaseAIProvider,
    AIConfigurationError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    AIResponseParseError
)
from backend.app.core.config import settings

class OpenAIProvider(BaseAIProvider):
    provider_id = "openai"
    name = "OpenAI (GPT Models)"
    is_local = False

    def is_configured(self) -> bool:
        return bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip())

    def get_status_message(self) -> str:
        if self.is_configured():
            return f"Configured for model '{settings.OPENAI_MODEL}' via {settings.OPENAI_BASE_URL}"
        return (
            "OpenAI API key not set. Set OPENAI_API_KEY in your .env file. "
            "Get an API key at https://platform.openai.com/api-keys"
        )

    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            raise AIConfigurationError(
                "OpenAI is not configured. Set OPENAI_API_KEY in your environment or .env file."
            )

        start_time = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "success": True,
                    "provider_id": self.provider_id,
                    "model": settings.OPENAI_MODEL,
                    "message": f"Successfully connected to OpenAI ({settings.OPENAI_MODEL})",
                    "latency_ms": latency_ms
                }
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 401:
                raise AIConfigurationError(
                    "OpenAI authentication failed: Invalid or expired API key (HTTP 401)."
                ) from e
            elif status_code == 429:
                raise AIRateLimitError(
                    "OpenAI rate limit or usage quota exceeded (HTTP 429). Check your billing balance at platform.openai.com."
                ) from e
            elif status_code == 404:
                raise AIConfigurationError(
                    f"Configured OpenAI model '{settings.OPENAI_MODEL}' not found or endpoint unreachable (HTTP 404)."
                ) from e
            else:
                raise AIProviderError(
                    f"OpenAI service returned HTTP {status_code}: {e.response.text[:200]}"
                ) from e
        except httpx.TimeoutException as e:
            raise AITimeoutError(
                f"OpenAI connection timed out after {settings.AI_REQUEST_TIMEOUT}s."
            ) from e
        except httpx.RequestError as e:
            raise AIProviderError(
                f"Network connection to OpenAI failed: {str(e)}"
            ) from e

    async def generate_structured_draft(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise AIConfigurationError(
                "OpenAI is not configured. Please set OPENAI_API_KEY in your .env file."
            )

        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": max_tokens,
            "temperature": 0.2
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 401:
                raise AIConfigurationError(
                    "OpenAI authentication failed: Invalid or expired API key (HTTP 401)."
                ) from e
            elif status_code == 429:
                raise AIRateLimitError(
                    "OpenAI rate limit or quota exceeded (HTTP 429). Check your OpenAI account."
                ) from e
            else:
                raise AIProviderError(
                    f"OpenAI generation returned HTTP {status_code}: {e.response.text[:200]}"
                ) from e
        except httpx.TimeoutException as e:
            raise AITimeoutError(
                f"OpenAI request timed out after {timeout} seconds."
            ) from e
        except httpx.RequestError as e:
            raise AIProviderError(
                f"Network request to OpenAI failed: {str(e)}"
            ) from e

        # Extract content from response
        try:
            content_str = data["choices"][0]["message"]["content"]
            parsed = json.loads(content_str)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON root must be a dictionary")
            return parsed
        except (KeyError, IndexError, json.JSONDecodeError, ValueError) as e:
            raise AIResponseParseError(
                f"OpenAI response was not valid structured JSON: {str(e)}"
            ) from e
