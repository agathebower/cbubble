"""LLM provider manager with fallback logic."""

import logging
from .base import BaseLLMProvider, LLMResponse
from .cerebras_provider import CerebrasProvider
from .groq_provider import GroqProvider
from ..config import AppConfig

log = logging.getLogger("cbubble.llm.manager")

PROVIDER_CLASSES = {"cerebras": CerebrasProvider, "groq": GroqProvider}


class LLMManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.providers: dict[str, BaseLLMProvider] = {}
        self._init_providers()

    def _init_providers(self):
        for name, pcfg in self.config.llm_providers.items():
            cls = PROVIDER_CLASSES.get(name)
            if not cls:
                log.warning("Unknown provider: %s", name); continue
            if not pcfg.api_key:
                log.warning("Skipping provider %s: no API key", name); continue
            self.providers[name] = cls(
                api_key=pcfg.api_key, base_url=pcfg.base_url, model=pcfg.model,
                max_tokens=pcfg.max_tokens, temperature=pcfg.temperature,
            )
            log.info("Initialized provider: %s", self.providers[name])

    @property
    def active(self) -> BaseLLMProvider | None:
        return self.providers.get(self.config.active_provider)

    @property
    def fallback(self) -> BaseLLMProvider | None:
        return self.providers.get(self.config.fallback_provider)

    async def complete(self, system_prompt, user_prompt) -> LLMResponse:
        provider = self.active
        if not provider:
            return LLMResponse(text="", provider="none", model="none",
                               success=False, error="No active provider configured")
        result = await provider.complete(system_prompt, user_prompt)
        if not result.success and self.config.auto_fallback_on_error:
            fb = self.fallback
            if fb and fb.name != provider.name:
                log.warning("Primary %s failed (%s), falling back to %s",
                            provider.name, result.error, fb.name)
                result = await fb.complete(system_prompt, user_prompt)
        return result

    def reload(self, config: AppConfig):
        self.config = config
        self.providers.clear()
        self._init_providers()
