"""
OpenRouter client for DRIPE LLM operations.
Uses OpenAI-compatible chat completions API via OpenRouter.
"""
import httpx
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0

OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"


def _get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        logger.warning("OPENROUTER_API_KEY not set in .env")
    return key


def _get_model() -> str:
    return os.getenv("LLM_MODEL", "openrouter/free")


class LLMClient:
    """Async HTTP client for OpenRouter API."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def generate(self, prompt: str, system: str = "") -> str:
        api_key = _get_api_key()
        if not api_key:
            return "LLM error: No API key configured."

        model = _get_model()
        try:
            client = await self._get_client()

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 512,
            }

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            response = await client.post(
                OPENROUTER_BASE,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if content is None:
                logger.warning("OpenRouter returned null content")
                return "LLM returned empty response."
            return content.strip()

        except httpx.TimeoutException:
            logger.warning(f"OpenRouter timeout ({self.timeout}s)")
            return "Timeout: LLM generation exceeded time limit."
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter HTTP error: {e}")
            return f"LLM error: {e.response.status_code}"
        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            return f"LLM error: {str(e)}"

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
