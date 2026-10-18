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

class AnthropicProvider(BaseAIProvider):
    provider_id = "anthropic"
    name = "Anthropic (Claude Models)"
    is_local = False

    def is_configured(self) -> bool:
        return bool(settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY.strip())

    def get_status_message(self) -> str:
        if self.is_configured():
            return f"Configured for model '{settings.ANTHROPIC_MODEL}' via {settings.ANTHROPIC_BASE_URL}"
        return (
            "Anthropic API key not set. Set ANTHROPIC_API_KEY in your .env file. "
            "Get an API key at https://console.anthropic.com/"
        )

    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            raise AIConfigurationError(
                "Anthropic is not configured. Set ANTHROPIC_API_KEY in your environment or .env file."
            )

        start_time = time.perf_counter()
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY.strip(),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": settings.ANTHROPIC_MODEL,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}]
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{settings.ANTHROPIC_BASE_URL.rstrip('/')}/messages",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "success": True,
                    "provider_id": self.provider_id,
                    "model": settings.ANTHROPIC_MODEL,
                    "message": f"Successfully connected to Anthropic ({settings.ANTHROPIC_MODEL})",
                    "latency_ms": latency_ms
                }
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 401:
                raise AIConfigurationError(
                    "Anthropic authentication failed: Invalid or expired API key (HTTP 401)."
                ) from e
            elif status_code == 429:
                raise AIRateLimitError(
                    "Anthropic rate limit or credit quota exceeded (HTTP 429). Check console.anthropic.com."
                ) from e
            elif status_code == 404:
                raise AIConfigurationError(
                    f"Configured Anthropic model '{settings.ANTHROPIC_MODEL}' not found or endpoint invalid (HTTP 404)."
                ) from e
            else:
                raise AIProviderError(
                    f"Anthropic service returned HTTP {status_code}: {e.response.text[:200]}"
                ) from e
        except httpx.TimeoutException as e:
            raise AITimeoutError(
                f"Anthropic connection timed out after {settings.AI_REQUEST_TIMEOUT}s."
            ) from e
        except httpx.RequestError as e:
            raise AIProviderError(
                f"Network connection to Anthropic failed: {str(e)}"
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
                "Anthropic is not configured. Please set ANTHROPIC_API_KEY in your .env file."
            )

        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY.strip(),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        augmented_system = (
            f"{system_prompt}\n\n"
            "CRITICAL INSTRUCTION: You MUST output ONLY the raw JSON object. "
            "Do NOT include markdown formatting like ```json ... ```, conversational commentary, or explanations."
        )

        payload = {
            "model": settings.ANTHROPIC_MODEL,
            "system": augmented_system,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{settings.ANTHROPIC_BASE_URL.rstrip('/')}/messages",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 401:
                raise AIConfigurationError(
                    "Anthropic authentication failed: Invalid or expired API key (HTTP 401)."
                ) from e
            elif status_code == 429:
                raise AIRateLimitError(
                    "Anthropic rate limit or quota exceeded (HTTP 429). Check console.anthropic.com."
                ) from e
            else:
                raise AIProviderError(
                    f"Anthropic generation returned HTTP {status_code}: {e.response.text[:200]}"
                ) from e
        except httpx.TimeoutException as e:
            raise AITimeoutError(
                f"Anthropic request timed out after {timeout} seconds."
            ) from e
        except httpx.RequestError as e:
            raise AIProviderError(
                f"Network request to Anthropic failed: {str(e)}"
            ) from e

        # Extract text content from Anthropic content blocks
        try:
            text_blocks = [
                b.get("text", "")
                for b in data.get("content", [])
                if b.get("type") == "text"
            ]
            raw_text = "".join(text_blocks).strip()

            # Clean markdown code blocks if model wrapped it anyway
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text)
            cleaned = re.sub(r"\s*```$", "", cleaned).strip()

            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON root must be a dictionary")
            return parsed
        except (KeyError, IndexError, json.JSONDecodeError, ValueError) as e:
            raise AIResponseParseError(
                f"Anthropic response was not valid structured JSON: {str(e)}"
            ) from e
