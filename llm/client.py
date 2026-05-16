"""
OpenRouter client for DRIPE LLM operations.
Uses OpenAI-compatible chat completions API via OpenRouter.
"""
import asyncio
import httpx
import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"

PRIMARY_MODEL = "openrouter/free"
SECONDARY_MODEL = "openrouter/auto"
PRIMARY_TIMEOUT = 30.0
SECONDARY_TIMEOUT = 45.0
RETRY_DELAY = 2.0
MAX_RETRIES = 1

_paid_call_count = 0


def _paid_fallback_allowed() -> bool:
    return os.getenv("LLM_DISABLE_PAID_FALLBACK", "").lower() not in ("true", "1")


def _paid_session_cap() -> int:
    return int(os.getenv("LLM_PAID_SESSION_CAP", "10"))


def check_spend() -> bool:
    global _paid_call_count
    if not _paid_fallback_allowed():
        return False
    return _paid_call_count < _paid_session_cap()


def increment_spend() -> int:
    global _paid_call_count
    _paid_call_count += 1
    logger.info(f"Paid fallback call {_paid_call_count}/{_paid_session_cap()} used")
    return _paid_call_count


def reset_spend_counter():
    global _paid_call_count
    _paid_call_count = 0


class LLMClient:
    """Async HTTP client for OpenRouter API with retry support."""

    def __init__(self, timeout: float = PRIMARY_TIMEOUT):
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self, timeout: float) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client

    async def generate(
        self,
        prompt: str,
        system: str = "",
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Tuple[str, bool]:
        """Generate text. Returns (response_text, success).
        Retries once on transient failures (null content, timeout).
        HTTP 4xx/5xx are non-retryable.
        """
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            logger.warning("OPENROUTER_API_KEY not set in .env")
            return "LLM error: No API key configured.", False

        model = model or os.getenv("LLM_MODEL", PRIMARY_MODEL)
        effective_timeout = timeout if timeout is not None else self.timeout

        payload = {
            "model": model,
            "messages": [],
            "temperature": 0.3,
            "max_tokens": 512,
        }
        if system:
            payload["messages"].append({"role": "system", "content": system})
        payload["messages"].append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(1 + MAX_RETRIES):
            try:
                client = await self._get_client(effective_timeout)
                response = await client.post(OPENROUTER_BASE, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                if content is None:
                    logger.warning(f"null content from {model} (attempt {attempt+1})")
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY)
                    continue
                return content.strip(), True
            except httpx.TimeoutException:
                logger.warning(f"timeout {model} (attempt {attempt+1})")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)
                continue
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} from {model}")
                return f"LLM error: {e.response.status_code}", False
            except Exception as e:
                logger.error(f"unexpected error from {model}: {e}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)
                continue

        return "LLM error after retries.", False

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


_client_instance: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClient()
    return _client_instance
