"""
Ollama client for DRIPE LLM operations.
Uses native Ollama REST API with httpx.
"""
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"
DEFAULT_TIMEOUT = 120.0


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url
        self.model = model
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
        return self._client

    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate text from Ollama."""
        try:
            client = await self._get_client()
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 512
                }
            }
            
            if system:
                payload["system"] = system

            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "").strip()

        except httpx.TimeoutException:
            logger.warning(f"Ollama timeout ({DEFAULT_TIMEOUT}s)")
            return "Timeout: LLM generation exceeded time limit."
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama HTTP error: {e}")
            return f"LLM error: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"LLM error: {str(e)}"

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get singleton Ollama client."""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
