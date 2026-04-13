"""Configuration loader."""

import json
import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from urllib.parse import urlparse

log = logging.getLogger("cbubble.config")

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "config.json"
LLM_DIR = CONFIG_DIR / "llm_providers"


_ALLOWED_SOURCE_SCHEMES = {"http", "https"}


def _validate_source_url(url: str, field_name: str) -> str:
    """Reject non-http(s) schemes in config URLs (prevents file://, gopher://, etc.)."""
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SOURCE_SCHEMES:
        raise ValueError(
            f"Source {field_name!r} has disallowed scheme {parsed.scheme!r}. "
            "Only http/https are permitted."
        )
    return url


@dataclass
class Source:
    name: str
    url: str
    category: str
    rss: str | None = None
    enabled: bool = True

    def __post_init__(self):
        _validate_source_url(self.url, "url")
        if self.rss:
            _validate_source_url(self.rss, "rss")


@dataclass
class CerebrasConfig:
    base_url: str
    abstract_api_key_env: str
    validate_api_key_env: str
    max_tokens: int = 1024
    temperature: float = 0.3
    requests_per_minute: int = 30

    @property
    def abstract_api_key(self) -> str:
        key = os.getenv(self.abstract_api_key_env, "")
        if not key:
            log.warning("API key env var %s is not set", self.abstract_api_key_env)
        return key

    @property
    def validate_api_key(self) -> str:
        key = os.getenv(self.validate_api_key_env, "")
        if not key:
            log.warning("API key env var %s is not set", self.validate_api_key_env)
        return key


@dataclass
class AppConfig:
    refresh_interval_minutes: int = 30
    max_abstract_sentences: int = 5
    stories_per_page: int = 20
    sources: list[Source] = field(default_factory=list)
    cerebras: CerebrasConfig | None = None
    notify_keywords: list[str] = field(default_factory=list)


def _load_cerebras_config() -> CerebrasConfig | None:
    cfg_file = LLM_DIR / "cerebras.json"
    if not cfg_file.exists():
        log.warning("Cerebras config not found: %s", cfg_file)
        return None
    try:
        data = json.loads(cfg_file.read_text())
        data.pop("provider", None)
        return CerebrasConfig(**data)
    except Exception as e:
        log.error("Failed to load Cerebras config: %s", e)
        return None


def load_config() -> AppConfig:
    """Load main config + Cerebras provider config."""
    try:
        data = json.loads(CONFIG_FILE.read_text())
    except Exception as e:
        log.error("Failed to load config.json: %s", e)
        data = {}

    sources = [Source(**s) for s in data.pop("sources", [])]
    cerebras = _load_cerebras_config()

    cfg = AppConfig(
        sources=sources,
        cerebras=cerebras,
        **{k: v for k, v in data.items() if k in AppConfig.__dataclass_fields__},
    )
    log.info(
        "Config loaded: %d sources, cerebras=%s",
        len(cfg.sources), "yes" if cerebras else "no",
    )
    return cfg
