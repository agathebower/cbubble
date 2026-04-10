"""Cerebras LLM provider (OpenAI-compatible API)."""

import re
import httpx
import logging
from .base import BaseLLMProvider, LLMResponse

_KEY_PATTERN = re.compile(r"(sk|csk)-[A-Za-z0-9\-]{10,}")


def _redact(text: str) -> str:
    """Replace any API key patterns in text with [REDACTED]."""
    return _KEY_PATTERN.sub("[REDACTED]", text)

log = logging.getLogger("cbubble.llm.cerebras")


class CerebrasProvider(BaseLLMProvider):
    def __init__(self, api_key, base_url, model, **kwargs):
        super().__init__(name="cerebras", api_key=api_key, base_url=base_url,
                         model=model, **kwargs)

    async def complete(self, system_prompt, user_prompt) -> LLMResponse:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model, "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.base_url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                log.info("Cerebras OK: %d chars, model=%s", len(text), self.model)
                return LLMResponse(text=text, provider=self.name, model=self.model,
                                   success=True, usage=data.get("usage"))
        except httpx.HTTPStatusError as e:
            safe_body = _redact(e.response.text[:200])
            log.error("Cerebras HTTP error %s: %s", e.response.status_code, safe_body)
            return LLMResponse(text="", provider=self.name, model=self.model,
                               success=False, error=f"HTTP {e.response.status_code}")
        except Exception as e:
            log.error("Cerebras request failed: %s", _redact(str(e)))
            return LLMResponse(text="", provider=self.name, model=self.model,
                               success=False, error=str(e))
