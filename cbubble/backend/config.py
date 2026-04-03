"""Configuration loader with auto-reload support."""

import json
import os
import logging
from pathlib import Path
from dataclasses import dataclass, field

log = logging.getLogger("cbubble.config")

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "config.json"
LLM_DIR = CONFIG_DIR / "llm_providers"


@dataclass
class Source:
    name: str
    url: str
    category: str
    rss: str | None = None
    enabled: bool = True


@dataclass
class LLMProviderConfig:
    provider: str
    api_key_env: str
    base_url: str
    model: str
    max_tokens: int = 1024
    temperature: float = 0.3
    requests_per_minute: int = 30

    @property
    def api_key(self) -> str:
        key = os.getenv(self.api_key_env, "")
        if not key:
            log.warning("API key env var %s is not set", self.api_key_env)
        return key


@dataclass
class AppConfig:
    active_provider: str = "cerebras"
    fallback_provider: str = "groq"
    auto_fallback_on_error: bool = True
    refresh_interval_minutes: int = 30
    max_abstract_sentences: int = 5
    stories_per_page: int = 20
    sources: list[Source] = field(default_factory=list)
    llm_providers: dict[str, LLMProviderConfig] = field(default_factory=dict)


def _load_llm_providers() -> dict[str, LLMProviderConfig]:
    providers = {}
    if not LLM_DIR.exists():
        log.warning("LLM providers directory not found: %s", LLM_DIR)
        return providers
    for f in LLM_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            providers[data["provider"]] = LLMProviderConfig(**data)
            log.info("Loaded LLM provider: %s (%s)", data["provider"], data["model"])
        except Exception as e:
            log.error("Failed to load LLM provider config %s: %s", f.name, e)
    return providers


def load_config() -> AppConfig:
    """Load main config + LLM provider configs. Call again to reload."""
    try:
        data = json.loads(CONFIG_FILE.read_text())
    except Exception as e:
        log.error("Failed to load config.json: %s", e)
        data = {}

    sources = [Source(**s) for s in data.pop("sources", [])]
    providers = _load_llm_providers()

    cfg = AppConfig(
        sources=sources,
        llm_providers=providers,
        **{k: v for k, v in data.items() if k in AppConfig.__dataclass_fields__},
    )
    log.info(
        "Config loaded: %d sources, %d providers, active=%s",
        len(cfg.sources), len(cfg.llm_providers), cfg.active_provider,
    )
    return cfg
