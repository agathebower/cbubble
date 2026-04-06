"""LLM manager — dual-role Cerebras (abstract + validate)."""

import logging
from .cerebras_provider import CerebrasProvider
from ..config import AppConfig

log = logging.getLogger("cbubble.llm.manager")


class LLMManager:
    def __init__(self, config: AppConfig, model: str):
        self.config = config
        self.model = model
        self.abstract_provider: CerebrasProvider | None = None
        self.validate_provider: CerebrasProvider | None = None
        self._init_providers()

    def _init_providers(self):
        cc = self.config.cerebras
        if not cc:
            log.error("No Cerebras config loaded"); return

        if cc.abstract_api_key:
            self.abstract_provider = CerebrasProvider(
                api_key=cc.abstract_api_key, base_url=cc.base_url,
                model=self.model, max_tokens=cc.max_tokens, temperature=cc.temperature,
            )
            log.info("Abstract provider ready: %s", self.abstract_provider)
        else:
            log.error("No API key for abstract provider")

        if cc.validate_api_key:
            self.validate_provider = CerebrasProvider(
                api_key=cc.validate_api_key, base_url=cc.base_url,
                model=self.model, max_tokens=cc.max_tokens, temperature=cc.temperature,
            )
            log.info("Validate provider ready: %s", self.validate_provider)
        else:
            log.error("No API key for validate provider")

    def update_model(self, model: str):
        """Update the model on both providers (called by model discovery)."""
        old = self.model
        self.model = model
        if self.abstract_provider:
            self.abstract_provider.model = model
        if self.validate_provider:
            self.validate_provider.model = model
        if old != model:
            log.info("Model updated: %s -> %s", old, model)
