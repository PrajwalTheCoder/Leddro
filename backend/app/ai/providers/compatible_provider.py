import time
import json
import re
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

class OpenAICompatibleProvider(BaseAIProvider):
    provider_id = "compatible"
    name = "Local / Self-Hosted (Ollama / vLLM / OpenAI-Compatible)"
    is_local = True

    def is_configured(self) -> bool:
        return bool(settings.COMPATIBLE_BASE_URL and settings.COMPATIBLE_BASE_URL.strip())

    def get_status_message(self) -> str:
        if self.is_configured():
            return (
                f"Configured for endpoint '{settings.COMPATIBLE_BASE_URL}' "
                f"using model '{settings.COMPATIBLE_MODEL}' (Local/Self-hosted)"
            )
        return "OpenAI-compatible base URL not configured. Set COMPATIBLE_BASE_URL in your .env file."

    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            raise AIConfigurationError(
                "Compatible provider is not configured. Set COMPATIBLE_BASE_URL in .env."
            )

        start_time = time.perf_counter()
        headers = {"Content-Type": "application/json"}
        if settings.COMPATIBLE_API_KEY and settings.COMPATIBLE_API_KEY.strip():
            headers["Authorization"] = f"Bearer {settings.COMPATIBLE_API_KEY.strip()}"

        payload = {
            "model": settings.COMPATIBLE_MODEL,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{settings.COMPATIBLE_BASE_URL.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "success": True,
                    "provider_id": self.provider_id,
                    "model": settings.COMPATIBLE_MODEL,
                    "message": f"Successfully connected to local/compatible provider ({settings.COMPATIBLE_MODEL})",
                    "latency_ms": latency_ms
                }
        except httpx.ConnectError as e:
            raise AIConfigurationError(
                f"Could not connect to service at {settings.COMPATIBLE_BASE_URL}. "
                f"Ensure your local model server (e.g. Ollama: 'ollama serve' or 'ollama run {settings.COMPATIBLE_MODEL}') is running."
            ) from e
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 404:
                raise AIConfigurationError(
                    f"Model '{settings.COMPATIBLE_MODEL}' not found at {settings.COMPATIBLE_BASE_URL} (HTTP 404). "
                    f"If using Ollama, run 'ollama pull {settings.COMPATIBLE_MODEL}'."
                ) from e
            elif status_code == 401:
                raise AIConfigurationError(
                    "Compatible provider authentication failed (HTTP 401). Verify COMPATIBLE_API_KEY."
                ) from e
            elif status_code == 429:
                raise AIRateLimitError(
                    "Compatible provider rate limit reached (HTTP 429)."
                ) from e
            else:
                raise AIProviderError(
                    f"Compatible provider returned HTTP {status_code}: {e.response.text[:200]}"
                ) from e
        except httpx.TimeoutException as e:
            raise AITimeoutError(
                f"Connection to {settings.COMPATIBLE_BASE_URL} timed out after {settings.AI_REQUEST_TIMEOUT}s."
            ) from e
        except httpx.RequestError as e:
            raise AIProviderError(
                f"Request to compatible provider failed: {str(e)}"
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
                "Compatible provider is not configured. Set COMPATIBLE_BASE_URL in your .env file."
            )

        headers = {"Content-Type": "application/json"}
        if settings.COMPATIBLE_API_KEY and settings.COMPATIBLE_API_KEY.strip():
            headers["Authorization"] = f"Bearer {settings.COMPATIBLE_API_KEY.strip()}"

        augmented_system = (
            f"{system_prompt}\n\n"
            "CRITICAL: Output ONLY a valid JSON object matching the requested schema. "
            "Do not output markdown backticks or commentary."
        )

        payload = {
            "model": settings.COMPATIBLE_MODEL,
            "messages": [
                {"role": "system", "content": augmented_system},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": max_tokens,
            "temperature": 0.2
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{settings.COMPATIBLE_BASE_URL.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError as e:
            raise AIConfigurationError(
                f"Could not reach compatible service at {settings.COMPATIBLE_BASE_URL}. "
                f"Ensure your local model server (Ollama, vLLM, etc.) is running."
            ) from e
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            raise AIProviderError(
                f"Compatible provider returned HTTP {status_code}: {e.response.text[:200]}"
            ) from e
        except httpx.TimeoutException as e:
            raise AITimeoutError(
                f"Compatible provider timed out after {timeout} seconds."
            ) from e
        except httpx.RequestError as e:
            raise AIProviderError(
                f"Network request to compatible provider failed: {str(e)}"
            ) from e

        try:
            content_str = data["choices"][0]["message"]["content"]
            cleaned = re.sub(r"^```(?:json)?\s*", "", content_str.strip())
            cleaned = re.sub(r"\s*```$", "", cleaned).strip()
            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON root must be a dictionary")
            return parsed
        except (KeyError, IndexError, json.JSONDecodeError, ValueError) as e:
            raise AIResponseParseError(
                f"Compatible provider response was not valid structured JSON: {str(e)}"
            ) from e
