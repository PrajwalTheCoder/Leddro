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

class GeminiProvider(BaseAIProvider):
    provider_id = "gemini"
    name = "Google Gemini (Flash & Pro)"
    is_local = False

    def is_configured(self) -> bool:
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())

    def get_status_message(self) -> str:
        if self.is_configured():
            return f"Configured for model '{settings.GEMINI_MODEL}' via Google AI Studio API"
        return (
            "Gemini API key not set. Insert your Gemini API key from https://aistudio.google.com/app/apikey"
        )

    def _get_model_url(self, model: str) -> str:
        clean_model = model.strip()
        if clean_model.startswith("models/"):
            clean_model = clean_model[len("models/"):]
        base = settings.GEMINI_BASE_URL.rstrip("/")
        api_key = settings.GEMINI_API_KEY.strip()
        return f"{base}/models/{clean_model}?key={api_key}"

    def _get_api_url(self, model: str) -> str:
        # Strip any leading 'models/' if user typed it
        clean_model = model.strip()
        if clean_model.startswith("models/"):
            clean_model = clean_model[len("models/"):]
        base = settings.GEMINI_BASE_URL.rstrip("/")
        api_key = settings.GEMINI_API_KEY.strip()
        return f"{base}/models/{clean_model}:generateContent?key={api_key}"

    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            raise AIConfigurationError(
                "Gemini is not configured. Insert your Gemini API key."
            )

        start_time = time.perf_counter()
        url = self._get_model_url(settings.GEMINI_MODEL)

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                display_name = data.get("displayName") or settings.GEMINI_MODEL
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "success": True,
                    "provider_id": self.provider_id,
                    "model": settings.GEMINI_MODEL,
                    "message": f"Successfully connected to Google Gemini ({display_name}) via Google AI Studio API",
                    "latency_ms": latency_ms
                }
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            err_text = e.response.text[:250]
            if status_code in (400, 401, 403):
                raise AIConfigurationError(
                    f"Gemini authentication failed (HTTP {status_code}): Invalid API key or permission denied. {err_text}"
                ) from e
            elif status_code == 429:
                raise AIRateLimitError(
                    f"Gemini rate limit or quota exceeded (HTTP 429). Check your Google AI Studio quota."
                ) from e
            elif status_code == 404:
                raise AIConfigurationError(
                    f"Configured Gemini model '{settings.GEMINI_MODEL}' not found (HTTP 404). Check model name."
                ) from e
            else:
                raise AIProviderError(
                    f"Gemini service returned HTTP {status_code}: {err_text}"
                ) from e
        except httpx.TimeoutException as e:
            raise AITimeoutError(
                f"Gemini connection timed out after {settings.AI_REQUEST_TIMEOUT}s."
            ) from e
        except httpx.RequestError as e:
            raise AIProviderError(
                f"Network connection to Gemini failed: {str(e)}"
            ) from e

    async def generate_structured_draft(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise AIConfigurationError(
                "Gemini is not configured. Please insert your Gemini API key."
            )

        url = self._get_api_url(settings.GEMINI_MODEL)
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
                "maxOutputTokens": max_tokens
            }
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            err_text = e.response.text[:250]
            if status_code in (400, 401, 403):
                raise AIConfigurationError(
                    f"Gemini authentication failed (HTTP {status_code}): {err_text}"
                ) from e
            elif status_code == 429:
                raise AIRateLimitError(
                    f"Gemini rate limit or quota exceeded (HTTP 429): {err_text}"
                ) from e
            else:
                raise AIProviderError(
                    f"Gemini generation returned HTTP {status_code}: {err_text}"
                ) from e
        except httpx.TimeoutException as e:
            raise AITimeoutError(
                f"Gemini request timed out after {timeout} seconds."
            ) from e
        except httpx.RequestError as e:
            raise AIProviderError(
                f"Network request to Gemini failed: {str(e)}"
            ) from e

        # Extract text from response candidates
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned by Gemini")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise ValueError("No content parts in Gemini candidate")
            content_str = parts[0].get("text", "").strip()

            # Clean markdown codeblocks if model included ```json ... ```
            if content_str.startswith("```"):
                content_str = re.sub(r"^```(?:json)?\s*", "", content_str)
                content_str = re.sub(r"\s*```$", "", content_str)

            parsed = json.loads(content_str)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON root must be a dictionary")
            return parsed
        except (KeyError, IndexError, json.JSONDecodeError, ValueError) as e:
            raise AIResponseParseError(
                f"Gemini response was not valid structured JSON: {str(e)}"
            ) from e
