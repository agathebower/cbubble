#!/usr/bin/env bash
# =============================================================================
# cBubble Bootstrap Script
# Erzeugt die komplette Projektstruktur in einem Rutsch.
# Usage: chmod +x bootstrap_cbubble.sh && ./bootstrap_cbubble.sh
# Danach: cd cbubble && ./scripts/setup.sh
# =============================================================================
set -euo pipefail

PROJECT="cbubble"
echo "=== Creating $PROJECT project structure ==="
mkdir -p "$PROJECT"/{config/llm_providers,backend/{llm,feeds,abstracts,workers,api},frontend/{css,js},scripts}

# --- __init__.py files ---
for d in backend backend/llm backend/feeds backend/abstracts backend/workers backend/api; do
    touch "$PROJECT/$d/__init__.py"
done

# ==================== .gitignore ====================
cat > "$PROJECT/.gitignore" << 'GITIGNORE'
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
venv/
.venv/
.env
*.db
*.sqlite3
.DS_Store
Thumbs.db
.vscode/
.idea/
*.swp
*.swo
GITIGNORE

# ==================== .env.example ====================
cat > "$PROJECT/.env.example" << 'ENVEX'
# cBubble Environment Configuration
# Copy this to .env and fill in your keys

CEREBRAS_API_KEY=your_cerebras_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Optional: Override default host/port
CBUBBLE_HOST=0.0.0.0
CBUBBLE_PORT=8800
ENVEX

# ==================== requirements.txt ====================
cat > "$PROJECT/requirements.txt" << 'REQ'
fastapi==0.115.6
uvicorn[standard]==0.34.0
httpx==0.28.1
feedparser==6.0.11
beautifulsoup4==4.12.3
python-dotenv==1.0.1
aiosqlite==0.20.0
apscheduler==3.10.4
REQ

# ==================== config/config.json ====================
cat > "$PROJECT/config/config.json" << 'CONF'
{
  "active_provider": "cerebras",
  "fallback_provider": "groq",
  "auto_fallback_on_error": true,
  "refresh_interval_minutes": 30,
  "max_abstract_sentences": 5,
  "stories_per_page": 20,
  "sources": [
    {"name": "The Hacker News", "url": "https://thehackernews.com", "rss": "https://feeds.feedburner.com/TheHackersNews", "category": "cyber", "enabled": true},
    {"name": "BleepingComputer", "url": "https://bleepingcomputer.com", "rss": "https://www.bleepingcomputer.com/feed/", "category": "cyber", "enabled": true},
    {"name": "Dark Reading", "url": "https://darkreading.com", "rss": "https://www.darkreading.com/rss.xml", "category": "cyber", "enabled": true},
    {"name": "SecurityWeek", "url": "https://securityweek.com", "rss": "https://feeds.feedburner.com/securityweek", "category": "cyber", "enabled": true},
    {"name": "Cybersecurity Dive", "url": "https://cybersecuritydive.com", "rss": "https://www.cybersecuritydive.com/feeds/news/", "category": "cyber", "enabled": true},
    {"name": "Simon Willison's Blog", "url": "https://simonwillison.net", "rss": "https://simonwillison.net/atom/everything/", "category": "ai", "enabled": true},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog", "rss": "https://huggingface.co/blog/feed.xml", "category": "ai", "enabled": true},
    {"name": "LWN.net", "url": "https://lwn.net", "rss": "https://lwn.net/headlines/rss", "category": "dev", "enabled": true},
    {"name": "Lobsters", "url": "https://lobste.rs", "rss": "https://lobste.rs/rss", "category": "dev", "enabled": true},
    {"name": "Hacker News", "url": "https://news.ycombinator.com", "rss": "https://hnrss.org/frontpage", "category": "dev", "enabled": true},
    {"name": "PortSwigger Research", "url": "https://portswigger.net/research", "rss": "https://portswigger.net/research/rss", "category": "offensive", "enabled": true},
    {"name": "VulDB", "url": "https://vuldb.com", "rss": "https://vuldb.com/?rss.recent", "category": "offensive", "enabled": true},
    {"name": "Exploit Database", "url": "https://exploit-db.com", "rss": "https://www.exploit-db.com/rss.xml", "category": "offensive", "enabled": true},
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com", "rss": "https://krebsonsecurity.com/feed/", "category": "threat_intel", "enabled": true},
    {"name": "Recorded Future Blog", "url": "https://recordedfuture.com/blog", "rss": "https://www.recordedfuture.com/feed", "category": "threat_intel", "enabled": true}
  ]
}
CONF

# ==================== config/llm_providers/cerebras.json ====================
cat > "$PROJECT/config/llm_providers/cerebras.json" << 'LLM1'
{
  "provider": "cerebras",
  "api_key_env": "CEREBRAS_API_KEY",
  "base_url": "https://api.cerebras.ai/v1/chat/completions",
  "model": "llama-4-scout-17b-16e-instruct",
  "max_tokens": 1024,
  "temperature": 0.3,
  "requests_per_minute": 30
}
LLM1

# ==================== config/llm_providers/groq.json ====================
cat > "$PROJECT/config/llm_providers/groq.json" << 'LLM2'
{
  "provider": "groq",
  "api_key_env": "GROQ_API_KEY",
  "base_url": "https://api.groq.com/openai/v1/chat/completions",
  "model": "llama-3.3-70b-versatile",
  "max_tokens": 1024,
  "temperature": 0.3,
  "requests_per_minute": 30
}
LLM2

# ==================== backend/config.py ====================
cat > "$PROJECT/backend/config.py" << 'PYCONF'
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
PYCONF

# ==================== backend/database.py ====================
cat > "$PROJECT/backend/database.py" << 'PYDB'
"""SQLite database setup and access layer."""

import aiosqlite
import logging
from pathlib import Path
from datetime import datetime, timezone

log = logging.getLogger("cbubble.db")

DB_PATH = Path(__file__).resolve().parent.parent / "cbubble.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    image_url TEXT,
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    content_raw TEXT,
    abstract TEXT,
    abstract_status TEXT NOT NULL DEFAULT 'pending',
    verification_note TEXT,
    provider_used TEXT
);
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(abstract_status);
CREATE INDEX IF NOT EXISTS idx_stories_fetched ON stories(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_stories_url ON stories(url);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()
    log.info("Database initialized at %s", DB_PATH)


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def insert_story(source_name, category, title, url, image_url=None,
                        published_at=None, content_raw=None) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            cursor = await db.execute(
                """INSERT INTO stories
                   (source_name, category, title, url, image_url, published_at, fetched_at, content_raw)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (source_name, category, title, url, image_url, published_at,
                 datetime.now(timezone.utc).isoformat(), content_raw),
            )
            await db.commit()
            return cursor.lastrowid
        except aiosqlite.IntegrityError:
            return None


async def get_stories(page=1, limit=20, category=None) -> list[dict]:
    offset = (page - 1) * limit
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if category:
            rows = await db.execute_fetchall(
                """SELECT id, source_name, category, title, url, image_url,
                          published_at, fetched_at, abstract, abstract_status
                   FROM stories WHERE category = ?
                   ORDER BY fetched_at DESC LIMIT ? OFFSET ?""",
                (category, limit, offset),
            )
        else:
            rows = await db.execute_fetchall(
                """SELECT id, source_name, category, title, url, image_url,
                          published_at, fetched_at, abstract, abstract_status
                   FROM stories ORDER BY fetched_at DESC LIMIT ? OFFSET ?""",
                (limit, offset),
            )
        return [dict(r) for r in rows]


async def get_pending_stories(limit=10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            """SELECT id, title, url, content_raw FROM stories
               WHERE abstract_status = 'pending' AND content_raw IS NOT NULL
               ORDER BY fetched_at DESC LIMIT ?""", (limit,),
        )
        return [dict(r) for r in rows]


async def update_abstract(story_id, abstract, status, verification_note=None,
                           provider_used=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE stories SET abstract = ?, abstract_status = ?,
               verification_note = ?, provider_used = ? WHERE id = ?""",
            (abstract, status, verification_note, provider_used, story_id),
        )
        await db.commit()


async def get_story_detail(story_id) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await db.execute_fetchall(
            "SELECT * FROM stories WHERE id = ?", (story_id,)
        )
        return dict(row[0]) if row else None
PYDB

# ==================== backend/llm/base.py ====================
cat > "$PROJECT/backend/llm/base.py" << 'LLMBASE'
"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    success: bool
    error: str | None = None
    usage: dict | None = None


class BaseLLMProvider(ABC):
    def __init__(self, name, api_key, base_url, model, max_tokens=1024, temperature=0.3):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse: ...

    def __repr__(self):
        return f"<{self.__class__.__name__} model={self.model}>"
LLMBASE

# ==================== backend/llm/cerebras_provider.py ====================
cat > "$PROJECT/backend/llm/cerebras_provider.py" << 'LLMCER'
"""Cerebras LLM provider (OpenAI-compatible API)."""

import httpx
import logging
from .base import BaseLLMProvider, LLMResponse

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
            log.error("Cerebras HTTP error %s: %s", e.response.status_code, e.response.text[:200])
            return LLMResponse(text="", provider=self.name, model=self.model,
                               success=False, error=f"HTTP {e.response.status_code}")
        except Exception as e:
            log.error("Cerebras request failed: %s", e)
            return LLMResponse(text="", provider=self.name, model=self.model,
                               success=False, error=str(e))
LLMCER

# ==================== backend/llm/groq_provider.py ====================
cat > "$PROJECT/backend/llm/groq_provider.py" << 'LLMGROQ'
"""Groq LLM provider (OpenAI-compatible API)."""

import httpx
import logging
from .base import BaseLLMProvider, LLMResponse

log = logging.getLogger("cbubble.llm.groq")


class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key, base_url, model, **kwargs):
        super().__init__(name="groq", api_key=api_key, base_url=base_url,
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
                log.info("Groq OK: %d chars, model=%s", len(text), self.model)
                return LLMResponse(text=text, provider=self.name, model=self.model,
                                   success=True, usage=data.get("usage"))
        except httpx.HTTPStatusError as e:
            log.error("Groq HTTP error %s: %s", e.response.status_code, e.response.text[:200])
            return LLMResponse(text="", provider=self.name, model=self.model,
                               success=False, error=f"HTTP {e.response.status_code}")
        except Exception as e:
            log.error("Groq request failed: %s", e)
            return LLMResponse(text="", provider=self.name, model=self.model,
                               success=False, error=str(e))
LLMGROQ

# ==================== backend/llm/manager.py ====================
cat > "$PROJECT/backend/llm/manager.py" << 'LLMMGR'
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
LLMMGR

# ==================== backend/feeds/fetcher.py ====================
cat > "$PROJECT/backend/feeds/fetcher.py" << 'FEEDS'
"""RSS/Atom feed fetcher with HTML fallback."""

import httpx
import feedparser
import logging
from bs4 import BeautifulSoup
from dataclasses import dataclass

log = logging.getLogger("cbubble.feeds")
HEADERS = {"User-Agent": "cBubble/1.0 (Personal News Aggregator)"}


@dataclass
class FeedItem:
    title: str
    url: str
    source_name: str
    category: str
    image_url: str | None = None
    published_at: str | None = None
    content_snippet: str | None = None


async def fetch_rss(source_name, rss_url, category) -> list[FeedItem]:
    items = []
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(rss_url)
            resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:25]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue
            image = None
            if hasattr(entry, "media_content") and entry.media_content:
                image = entry.media_content[0].get("url")
            elif hasattr(entry, "enclosures") and entry.enclosures:
                enc = entry.enclosures[0]
                if enc.get("type", "").startswith("image"):
                    image = enc.get("href")
            content = ""
            if hasattr(entry, "summary"):
                content = BeautifulSoup(entry.summary, "html.parser").get_text()[:500]
            elif hasattr(entry, "content") and entry.content:
                content = BeautifulSoup(entry.content[0].value, "html.parser").get_text()[:500]
            published = entry.get("published", entry.get("updated"))
            items.append(FeedItem(title=title, url=link, source_name=source_name,
                                  category=category, image_url=image,
                                  published_at=published,
                                  content_snippet=content if content else None))
        log.info("Fetched %d items from %s", len(items), source_name)
    except Exception as e:
        log.error("Failed to fetch RSS from %s: %s", source_name, e)
    return items


async def fetch_article_content(url) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=20.0, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()
        article = soup.find("article") or soup.find("main") or soup.find("div", class_="post-content")
        text = (article or soup).get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        content = "\n".join(lines)[:8000]
        return content if len(content) > 100 else None
    except Exception as e:
        log.error("Failed to fetch article from %s: %s", url, e)
        return None
FEEDS

# ==================== backend/abstracts/engine.py ====================
cat > "$PROJECT/backend/abstracts/engine.py" << 'ENGINE'
"""Abstract generation and verification engine."""

import logging
from ..llm.manager import LLMManager

log = logging.getLogger("cbubble.abstracts")

SUMMARIZE_SYSTEM = """You are a precise news summarizer. Given an article's content, produce a concise factual abstract.
Rules:
- Maximum {max_sentences} sentences
- Focus only on verifiable facts, not opinions
- Include: who, what, when, where if available
- No editorializing or speculation
- If the content is too short or unclear, say "INSUFFICIENT_CONTENT"
"""

SUMMARIZE_USER = """Summarize this article into a brief factual abstract:

Title: {title}

Content:
{content}
"""

VERIFY_SYSTEM = """You are a fact-checking assistant. You will receive an original article and a generated abstract.
Your job is to verify the abstract against the original content.

Respond in this exact format:
VERDICT: VERIFIED or FLAGGED
ISSUES: None, or a brief description of any inaccuracies, omissions, or hallucinations found
CORRECTED: Only if FLAGGED, provide a corrected version of the abstract
"""

VERIFY_USER = """Original article title: {title}

Original content:
{content}

---

Generated abstract:
{abstract}

Verify this abstract against the original content.
"""


class AbstractEngine:
    def __init__(self, llm: LLMManager, max_sentences=5):
        self.llm = llm
        self.max_sentences = max_sentences

    async def generate(self, title, content) -> dict:
        # Step 1: Summarize
        sum_result = await self.llm.complete(
            system_prompt=SUMMARIZE_SYSTEM.format(max_sentences=self.max_sentences),
            user_prompt=SUMMARIZE_USER.format(title=title, content=content),
        )
        if not sum_result.success:
            return {"abstract": None, "status": "error",
                    "note": f"Summarization failed: {sum_result.error}",
                    "provider": sum_result.provider}

        abstract_text = sum_result.text.strip()
        if "INSUFFICIENT_CONTENT" in abstract_text:
            return {"abstract": None, "status": "skipped",
                    "note": "Content too short or unclear",
                    "provider": sum_result.provider}

        # Step 2: Verify
        ver_result = await self.llm.complete(
            system_prompt=VERIFY_SYSTEM,
            user_prompt=VERIFY_USER.format(title=title, content=content, abstract=abstract_text),
        )
        if not ver_result.success:
            return {"abstract": abstract_text, "status": "unverified",
                    "note": f"Verification failed: {ver_result.error}",
                    "provider": sum_result.provider}

        ver_text = ver_result.text.strip()
        if "VERDICT: VERIFIED" in ver_text:
            return {"abstract": abstract_text, "status": "verified",
                    "note": None, "provider": sum_result.provider}
        elif "VERDICT: FLAGGED" in ver_text:
            corrected = abstract_text
            if "CORRECTED:" in ver_text:
                corrected_part = ver_text.split("CORRECTED:", 1)[1].strip()
                if corrected_part and len(corrected_part) > 20:
                    corrected = corrected_part
            issues = ""
            if "ISSUES:" in ver_text:
                issues = ver_text.split("ISSUES:", 1)[1].split("CORRECTED:")[0].strip()
            return {"abstract": corrected, "status": "flagged",
                    "note": issues or "Verification flagged issues",
                    "provider": sum_result.provider}
        else:
            return {"abstract": abstract_text, "status": "unverified",
                    "note": "Could not parse verification response",
                    "provider": sum_result.provider}
ENGINE

# ==================== backend/workers/feed_worker.py ====================
cat > "$PROJECT/backend/workers/feed_worker.py" << 'WF'
"""Periodic feed collection worker."""

import asyncio
import logging
from ..config import AppConfig, Source
from ..feeds.fetcher import fetch_rss, fetch_article_content
from ..database import insert_story, get_db

log = logging.getLogger("cbubble.worker.feed")


async def collect_source(source: Source):
    if not source.enabled or not source.rss:
        return 0
    items = await fetch_rss(source.name, source.rss, source.category)
    new_count = 0
    for item in items:
        story_id = await insert_story(
            source_name=item.source_name, category=item.category,
            title=item.title, url=item.url, image_url=item.image_url,
            published_at=item.published_at, content_raw=item.content_snippet,
        )
        if story_id:
            new_count += 1
            content = await fetch_article_content(item.url)
            if content:
                db = await get_db()
                try:
                    await db.execute("UPDATE stories SET content_raw = ? WHERE id = ?",
                                     (content, story_id))
                    await db.commit()
                finally:
                    await db.close()
    if new_count:
        log.info("Source %s: %d new stories", source.name, new_count)
    return new_count


async def collect_all(config: AppConfig):
    log.info("Starting feed collection for %d sources", len(config.sources))
    total = 0
    for source in config.sources:
        try:
            count = await collect_source(source)
            total += count
        except Exception as e:
            log.error("Failed to collect from %s: %s", source.name, e)
        await asyncio.sleep(1)
    log.info("Feed collection complete: %d new stories total", total)
    return total
WF

# ==================== backend/workers/abstract_worker.py ====================
cat > "$PROJECT/backend/workers/abstract_worker.py" << 'WA'
"""Background worker for generating abstracts."""

import asyncio
import logging
from ..database import get_pending_stories, update_abstract
from ..abstracts.engine import AbstractEngine

log = logging.getLogger("cbubble.worker.abstract")


async def process_pending(engine: AbstractEngine, batch_size=5):
    stories = await get_pending_stories(limit=batch_size)
    if not stories:
        return 0
    log.info("Processing %d pending abstracts", len(stories))
    processed = 0
    for story in stories:
        if not story["content_raw"]:
            await update_abstract(story["id"], "", "skipped", "No content available")
            continue
        try:
            result = await engine.generate(title=story["title"], content=story["content_raw"])
            await update_abstract(
                story_id=story["id"], abstract=result["abstract"] or "",
                status=result["status"], verification_note=result["note"],
                provider_used=result["provider"],
            )
            processed += 1
            log.info("Abstract for '%s': %s (provider: %s)",
                     story["title"][:50], result["status"], result["provider"])
        except Exception as e:
            log.error("Failed abstract for story %d: %s", story["id"], e)
            await update_abstract(story["id"], "", "error", str(e))
        await asyncio.sleep(2)
    return processed
WA

# ==================== backend/api/routes.py ====================
cat > "$PROJECT/backend/api/routes.py" << 'ROUTES'
"""REST API routes."""

from fastapi import APIRouter, Query, HTTPException
from ..database import get_stories, get_story_detail
from ..config import load_config

router = APIRouter(prefix="/api")


@router.get("/stories")
async def list_stories(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
                       category: str | None = Query(None)):
    stories = await get_stories(page=page, limit=limit, category=category)
    return {"stories": stories, "page": page, "limit": limit}


@router.get("/stories/{story_id}")
async def story_detail(story_id: int):
    story = await get_story_detail(story_id)
    if not story:
        raise HTTPException(404, "Story not found")
    return story


@router.get("/categories")
async def list_categories():
    config = load_config()
    cats = sorted(set(s.category for s in config.sources if s.enabled))
    return {"categories": cats}


@router.get("/sources")
async def list_sources():
    config = load_config()
    return {"sources": [{"name": s.name, "url": s.url, "category": s.category,
                          "enabled": s.enabled} for s in config.sources]}


@router.post("/reload")
async def reload_config():
    config = load_config()
    return {"status": "reloaded", "sources": len(config.sources),
            "active_provider": config.active_provider}
ROUTES

# ==================== backend/main.py ====================
cat > "$PROJECT/backend/main.py" << 'MAIN'
"""cBubble — Custom News Feed Aggregator."""

import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pathlib import Path

from .config import load_config
from .database import init_db
from .llm.manager import LLMManager
from .abstracts.engine import AbstractEngine
from .workers.feed_worker import collect_all
from .workers.abstract_worker import process_pending
from .api.routes import router as api_router

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger("cbubble")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

config = None
llm_manager = None
abstract_engine = None
scheduler = AsyncIOScheduler()


async def scheduled_feed_collect():
    await collect_all(config)
    await process_pending(abstract_engine, batch_size=10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global config, llm_manager, abstract_engine
    config = load_config()
    await init_db()
    llm_manager = LLMManager(config)
    abstract_engine = AbstractEngine(llm_manager, config.max_abstract_sentences)
    scheduler.add_job(scheduled_feed_collect, "interval",
                      minutes=config.refresh_interval_minutes,
                      id="feed_collect", replace_existing=True)
    scheduler.start()
    log.info("Scheduler started: collecting every %d min", config.refresh_interval_minutes)
    log.info("Running initial feed collection...")
    await collect_all(config)
    await process_pending(abstract_engine, batch_size=10)
    yield
    scheduler.shutdown(wait=False)
    log.info("cBubble shut down.")


app = FastAPI(title="cBubble", version="0.1.0", lifespan=lifespan)
app.include_router(api_router)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/manifest.json")
    async def serve_manifest():
        return FileResponse(FRONTEND_DIR / "manifest.json")

    @app.get("/sw.js")
    async def serve_sw():
        return FileResponse(FRONTEND_DIR / "sw.js", media_type="application/javascript")
MAIN

# ==================== frontend/index.html ====================
cat > "$PROJECT/frontend/index.html" << 'HTML'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#0a0a0f">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>cBubble</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <header id="app-header">
        <div class="header-inner">
            <h1 class="logo">c<span>Bubble</span></h1>
            <div class="header-actions">
                <button id="btn-refresh" class="icon-btn" title="Refresh">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M23 4v6h-6M1 20v-6h6"/>
                        <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
                    </svg>
                </button>
            </div>
        </div>
        <nav id="category-tabs" class="category-tabs">
            <button class="cat-tab active" data-category="all">All</button>
        </nav>
    </header>
    <main id="feed" class="feed-grid"></main>
    <div id="loader" class="loader"><div class="spinner"></div><span>Loading stories…</span></div>
    <div id="empty-state" class="empty-state hidden">
        <p>No stories yet. Feeds are being collected…</p>
        <button id="btn-retry" class="btn-primary">Retry</button>
    </div>
    <div id="popup-overlay" class="popup-overlay hidden">
        <div class="popup-card">
            <div class="popup-header">
                <span class="popup-source"></span>
                <span class="popup-badge"></span>
                <button class="popup-close">&times;</button>
            </div>
            <h2 class="popup-title"></h2>
            <div class="popup-abstract">
                <div class="popup-loading">Generating abstract…</div>
                <p class="popup-text"></p>
            </div>
            <div class="popup-verification-note hidden"><small></small></div>
            <div class="popup-footer">
                <a class="popup-link" href="#" target="_blank" rel="noopener">Read full article →</a>
            </div>
        </div>
    </div>
    <script src="/static/js/app.js"></script>
    <script src="/static/js/feed.js"></script>
    <script src="/static/js/popup.js"></script>
</body>
</html>
HTML

# ==================== frontend/css/style.css ====================
cat > "$PROJECT/frontend/css/style.css" << 'CSS'
:root {
    --bg: #0a0a0f;
    --bg-card: #15151e;
    --bg-card-hover: #1c1c2a;
    --bg-popup: #1a1a28;
    --text: #e4e4ed;
    --text-muted: #8888a0;
    --accent: #6c5ce7;
    --accent-glow: #6c5ce740;
    --green: #00cec9;
    --yellow: #fdcb6e;
    --red: #ff6b6b;
    --border: #2a2a3d;
    --radius: 12px;
    --header-h: 100px;
}
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 15px; background: var(--bg); color: var(--text);
    -webkit-tap-highlight-color: transparent;
}
body { min-height: 100dvh; padding-top: var(--header-h); overflow-x: hidden; }
.hidden { display: none !important; }

#app-header {
    position: fixed; top: 0; left: 0; right: 0; z-index: 100;
    background: var(--bg); border-bottom: 1px solid var(--border);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}
.header-inner {
    display: flex; align-items: center; justify-content: space-between;
    max-width: 640px; margin: 0 auto; padding: 12px 16px 8px;
}
.logo { font-size: 1.4rem; font-weight: 700; letter-spacing: -0.5px; color: var(--text); }
.logo span { color: var(--accent); }
.icon-btn {
    background: none; border: none; color: var(--text-muted);
    cursor: pointer; padding: 6px; border-radius: 8px; transition: color .2s, background .2s;
}
.icon-btn:hover { color: var(--text); background: var(--bg-card); }
.category-tabs {
    display: flex; gap: 6px; max-width: 640px; margin: 0 auto;
    padding: 4px 16px 10px; overflow-x: auto; scrollbar-width: none;
}
.category-tabs::-webkit-scrollbar { display: none; }
.cat-tab {
    flex-shrink: 0; background: var(--bg-card); border: 1px solid var(--border);
    color: var(--text-muted); font-size: .8rem; font-weight: 500;
    padding: 5px 14px; border-radius: 20px; cursor: pointer;
    transition: all .2s; text-transform: capitalize;
}
.cat-tab:hover { color: var(--text); border-color: var(--text-muted); }
.cat-tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }

.feed-grid {
    max-width: 640px; margin: 0 auto; padding: 12px;
    display: flex; flex-direction: column; gap: 12px;
}
.tile {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--radius); overflow: hidden; cursor: pointer;
    transition: transform .15s, background .2s, box-shadow .2s;
    -webkit-user-select: none; user-select: none;
}
.tile:hover {
    background: var(--bg-card-hover);
    box-shadow: 0 0 20px var(--accent-glow); transform: translateY(-1px);
}
.tile:active { transform: scale(0.985); }
.tile-image { width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; background: var(--border); }
.tile-image-placeholder {
    width: 100%; aspect-ratio: 16/9;
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--border) 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem; color: var(--text-muted);
}
.tile-body { padding: 14px 16px; }
.tile-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.tile-source { font-size: .75rem; font-weight: 600; color: var(--accent); text-transform: uppercase; letter-spacing: .3px; }
.tile-time { font-size: .7rem; color: var(--text-muted); }
.tile-category { font-size: .65rem; color: var(--text-muted); background: var(--border); padding: 2px 8px; border-radius: 10px; margin-left: auto; }
.tile-title { font-size: 1rem; font-weight: 600; line-height: 1.35; color: var(--text); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.tile-snippet { font-size: .82rem; color: var(--text-muted); line-height: 1.45; margin-top: 6px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.tile-status { margin-top: 10px; display: flex; align-items: center; gap: 6px; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; }
.status-dot.verified { background: var(--green); }
.status-dot.flagged { background: var(--yellow); }
.status-dot.pending { background: var(--text-muted); }
.status-dot.error { background: var(--red); }
.status-label { font-size: .7rem; color: var(--text-muted); text-transform: capitalize; }

.loader { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 40px 0; color: var(--text-muted); }
.spinner { width: 28px; height: 28px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.empty-state { text-align: center; padding: 60px 20px; color: var(--text-muted); }
.btn-primary { margin-top: 16px; padding: 10px 24px; background: var(--accent); color: #fff; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: opacity .2s; }
.btn-primary:hover { opacity: .85; }

.popup-overlay {
    position: fixed; inset: 0; z-index: 200; background: rgba(0,0,0,.7);
    backdrop-filter: blur(6px); display: flex; align-items: flex-end;
    justify-content: center; padding: 20px; animation: fadeIn .2s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.popup-card {
    background: var(--bg-popup); border: 1px solid var(--border);
    border-radius: 16px 16px 8px 8px; width: 100%; max-width: 560px;
    max-height: 75dvh; overflow-y: auto; padding: 20px; animation: slideUp .25s ease;
}
@keyframes slideUp { from { transform: translateY(40px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.popup-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.popup-source { font-size: .75rem; font-weight: 600; color: var(--accent); text-transform: uppercase; }
.popup-badge { font-size: .65rem; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
.popup-badge.verified { background: var(--green); color: #000; }
.popup-badge.flagged { background: var(--yellow); color: #000; }
.popup-badge.unverified { background: var(--text-muted); color: #000; }
.popup-badge.pending { background: var(--border); color: var(--text-muted); }
.popup-close { margin-left: auto; background: none; border: none; color: var(--text-muted); font-size: 1.5rem; cursor: pointer; line-height: 1; padding: 0 4px; }
.popup-close:hover { color: var(--text); }
.popup-title { font-size: 1.15rem; font-weight: 700; line-height: 1.3; margin-bottom: 16px; }
.popup-abstract { margin-bottom: 16px; }
.popup-loading { color: var(--text-muted); font-style: italic; }
.popup-text { font-size: .92rem; line-height: 1.6; color: var(--text); }
.popup-verification-note small { display: block; padding: 8px 12px; background: var(--border); border-radius: 8px; color: var(--yellow); font-size: .78rem; line-height: 1.4; margin-bottom: 16px; }
.popup-footer { border-top: 1px solid var(--border); padding-top: 14px; }
.popup-link { color: var(--accent); text-decoration: none; font-weight: 600; font-size: .9rem; }
.popup-link:hover { text-decoration: underline; }
@media (min-width: 768px) { .popup-overlay { align-items: center; } .popup-card { border-radius: 16px; } }
CSS

# ==================== frontend/js/app.js ====================
cat > "$PROJECT/frontend/js/app.js" << 'APPJS'
const App = {
    state: { page: 1, loading: false, hasMore: true, category: null, stories: [] },
    async init() {
        await this.loadCategories();
        await Feed.loadPage();
        this.bindEvents();
        this.registerSW();
    },
    bindEvents() {
        document.getElementById("btn-refresh").addEventListener("click", () => this.refresh());
        document.getElementById("btn-retry")?.addEventListener("click", () => this.refresh());
    },
    async loadCategories() {
        try {
            const resp = await fetch("/api/categories");
            const data = await resp.json();
            const nav = document.getElementById("category-tabs");
            data.categories.forEach(cat => {
                const btn = document.createElement("button");
                btn.className = "cat-tab"; btn.dataset.category = cat;
                btn.textContent = cat.replace("_", " ");
                btn.addEventListener("click", () => this.setCategory(cat, btn));
                nav.appendChild(btn);
            });
            nav.querySelector('[data-category="all"]').addEventListener("click", (e) => {
                this.setCategory(null, e.target);
            });
        } catch (e) { console.error("Failed to load categories:", e); }
    },
    setCategory(cat, btn) {
        document.querySelectorAll(".cat-tab").forEach(t => t.classList.remove("active"));
        btn.classList.add("active");
        this.state.category = cat; this.state.page = 1;
        this.state.hasMore = true; this.state.stories = [];
        document.getElementById("feed").innerHTML = "";
        Feed.loadPage();
    },
    async refresh() {
        this.state.page = 1; this.state.hasMore = true; this.state.stories = [];
        document.getElementById("feed").innerHTML = "";
        try { await fetch("/api/reload", { method: "POST" }); } catch (_) {}
        await Feed.loadPage();
    },
    registerSW() {
        if ("serviceWorker" in navigator)
            navigator.serviceWorker.register("/sw.js").catch(e => console.warn("SW fail:", e));
    },
};
document.addEventListener("DOMContentLoaded", () => App.init());
APPJS

# ==================== frontend/js/feed.js ====================
cat > "$PROJECT/frontend/js/feed.js" << 'FEEDJS'
const CATEGORY_ICONS = { cyber: "🔐", ai: "🤖", dev: "🛠️", offensive: "🕵️", threat_intel: "📡" };
const Feed = {
    observer: null,
    async loadPage() {
        const s = App.state;
        if (s.loading || !s.hasMore) return;
        s.loading = true;
        const loader = document.getElementById("loader");
        const empty = document.getElementById("empty-state");
        loader.classList.remove("hidden"); empty.classList.add("hidden");
        try {
            let url = `/api/stories?page=${s.page}&limit=20`;
            if (s.category) url += `&category=${s.category}`;
            const resp = await fetch(url);
            const data = await resp.json();
            const stories = data.stories || [];
            if (stories.length === 0 && s.page === 1) empty.classList.remove("hidden");
            if (stories.length < 20) s.hasMore = false;
            stories.forEach(story => { s.stories.push(story); this.renderTile(story); });
            s.page++;
        } catch (e) { console.error("Failed to load stories:", e); }
        finally { s.loading = false; loader.classList.toggle("hidden", !s.hasMore); this.observeScroll(); }
    },
    renderTile(story) {
        const feed = document.getElementById("feed");
        const tile = document.createElement("article");
        tile.className = "tile"; tile.dataset.id = story.id; tile.dataset.url = story.url;
        const icon = CATEGORY_ICONS[story.category] || "📰";
        const timeAgo = this.timeAgo(story.published_at || story.fetched_at);
        let imageHTML = story.image_url
            ? `<img class="tile-image" src="${this.esc(story.image_url)}" alt="" loading="lazy" onerror="this.outerHTML='<div class=\\'tile-image-placeholder\\'>${icon}</div>'">`
            : `<div class="tile-image-placeholder">${icon}</div>`;
        tile.innerHTML = `${imageHTML}
            <div class="tile-body">
                <div class="tile-meta">
                    <span class="tile-source">${this.esc(story.source_name)}</span>
                    <span class="tile-time">${timeAgo}</span>
                    <span class="tile-category">${story.category.replace("_", " ")}</span>
                </div>
                <h3 class="tile-title">${this.esc(story.title)}</h3>
                <div class="tile-status">
                    <span class="status-dot ${story.abstract_status}"></span>
                    <span class="status-label">${story.abstract_status}</span>
                </div>
            </div>`;
        tile.addEventListener("click", (e) => { e.preventDefault(); Popup.open(story); });
        feed.appendChild(tile);
    },
    observeScroll() {
        if (this.observer) this.observer.disconnect();
        const loader = document.getElementById("loader");
        if (!App.state.hasMore) return;
        this.observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) this.loadPage();
        }, { rootMargin: "300px" });
        this.observer.observe(loader);
    },
    timeAgo(dateStr) {
        if (!dateStr) return "";
        try {
            const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
            if (diff < 60) return "just now";
            if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
            if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
            if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
            return new Date(dateStr).toLocaleDateString();
        } catch { return ""; }
    },
    esc(s) { if (!s) return ""; const d = document.createElement("div"); d.textContent = s; return d.innerHTML; },
};
FEEDJS

# ==================== frontend/js/popup.js ====================
cat > "$PROJECT/frontend/js/popup.js" << 'POPJS'
const Popup = {
    overlay: null, currentStory: null,
    init() {
        this.overlay = document.getElementById("popup-overlay");
        this.overlay.querySelector(".popup-close").addEventListener("click", () => this.close());
        this.overlay.addEventListener("click", (e) => { if (e.target === this.overlay) this.close(); });
        document.addEventListener("keydown", (e) => { if (e.key === "Escape") this.close(); });
    },
    async open(story) {
        this.currentStory = story;
        const o = this.overlay;
        o.querySelector(".popup-source").textContent = story.source_name;
        o.querySelector(".popup-title").textContent = story.title;
        o.querySelector(".popup-link").href = story.url;
        const badge = o.querySelector(".popup-badge");
        badge.textContent = story.abstract_status;
        badge.className = `popup-badge ${story.abstract_status}`;
        const textEl = o.querySelector(".popup-text");
        const loadingEl = o.querySelector(".popup-loading");
        const noteEl = o.querySelector(".popup-verification-note");
        noteEl.classList.add("hidden");
        if (story.abstract && story.abstract_status !== "pending") {
            loadingEl.classList.add("hidden");
            textEl.textContent = story.abstract; textEl.classList.remove("hidden");
        } else {
            loadingEl.classList.remove("hidden"); textEl.classList.add("hidden");
            await this.fetchDetail(story.id, textEl, loadingEl, badge, noteEl);
        }
        if (story.verification_note && story.abstract_status === "flagged") {
            noteEl.querySelector("small").textContent = `⚠️ ${story.verification_note}`;
            noteEl.classList.remove("hidden");
        }
        o.classList.remove("hidden"); document.body.style.overflow = "hidden";
    },
    async fetchDetail(storyId, textEl, loadingEl, badge, noteEl) {
        try {
            const resp = await fetch(`/api/stories/${storyId}`);
            const d = await resp.json();
            if (d.abstract) {
                textEl.textContent = d.abstract; textEl.classList.remove("hidden");
                loadingEl.classList.add("hidden");
                badge.textContent = d.abstract_status; badge.className = `popup-badge ${d.abstract_status}`;
                if (d.verification_note && d.abstract_status === "flagged") {
                    noteEl.querySelector("small").textContent = `⚠️ ${d.verification_note}`;
                    noteEl.classList.remove("hidden");
                }
            } else { loadingEl.textContent = "Abstract not yet available. Check back soon."; }
        } catch (e) { loadingEl.textContent = "Failed to load abstract."; console.error(e); }
    },
    close() { this.overlay.classList.add("hidden"); document.body.style.overflow = ""; this.currentStory = null; },
};
document.addEventListener("DOMContentLoaded", () => Popup.init());
POPJS

# ==================== frontend/manifest.json ====================
cat > "$PROJECT/frontend/manifest.json" << 'MANIFEST'
{
  "name": "cBubble — Custom News Feed",
  "short_name": "cBubble",
  "description": "AI-powered custom news aggregator",
  "start_url": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#0a0a0f",
  "theme_color": "#0a0a0f",
  "icons": [
    {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}
MANIFEST

# ==================== frontend/sw.js ====================
cat > "$PROJECT/frontend/sw.js" << 'SW'
const CACHE_NAME = "cbubble-v1";
const STATIC_ASSETS = ["/", "/static/css/style.css", "/static/js/app.js", "/static/js/feed.js", "/static/js/popup.js"];
self.addEventListener("install", (e) => {
    e.waitUntil(caches.open(CACHE_NAME).then((c) => c.addAll(STATIC_ASSETS)));
    self.skipWaiting();
});
self.addEventListener("activate", (e) => {
    e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))));
    self.clients.claim();
});
self.addEventListener("fetch", (e) => {
    const url = new URL(e.request.url);
    if (url.pathname.startsWith("/api/")) {
        e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    } else {
        e.respondWith(caches.match(e.request).then((c) => c || fetch(e.request)));
    }
});
SW

# ==================== scripts/setup.sh ====================
cat > "$PROJECT/scripts/setup.sh" << 'SETUP'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
echo "=== cBubble Setup ==="
cd "$PROJECT_DIR"
if [ ! -d "venv" ]; then
    echo "[+] Creating Python virtual environment..."
    python3 -m venv venv
fi
echo "[+] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
if [ ! -f ".env" ]; then
    echo "[+] Creating .env from .env.example..."
    cp .env.example .env
    echo "    ⚠️  Please edit .env and add your API keys!"
fi
for dir in backend backend/llm backend/feeds backend/abstracts backend/workers backend/api; do
    touch "$dir/__init__.py"
done
echo ""
echo "=== Setup complete ==="
echo "  1. Edit .env with your API keys"
echo "  2. Run: ./scripts/run.sh"
SETUP
chmod +x "$PROJECT/scripts/setup.sh"

# ==================== scripts/run.sh ====================
cat > "$PROJECT/scripts/run.sh" << 'RUN'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"
source venv/bin/activate
HOST="${CBUBBLE_HOST:-0.0.0.0}"
PORT="${CBUBBLE_PORT:-8800}"
echo "=== cBubble starting on http://${HOST}:${PORT} ==="
exec uvicorn backend.main:app --host "$HOST" --port "$PORT" --reload
RUN
chmod +x "$PROJECT/scripts/run.sh"

# ==================== README.md ====================
cat > "$PROJECT/README.md" << 'README'
# cBubble 🫧

Custom AI-powered news feed — a self-hosted news aggregator with Instagram-style UI
that uses LLMs to generate verified story abstracts.

## Quick Start

```bash
git clone https://github.com/YOUR_USER/cbubble.git
cd cbubble
./scripts/setup.sh
vim .env   # add CEREBRAS_API_KEY and/or GROQ_API_KEY
./scripts/run.sh
```

Open http://localhost:8800

## Features

- Custom RSS sources via JSON config
- AI abstracts with fact-check verification (Cerebras / Groq)
- Automatic provider fallback
- Instagram-style dark theme with infinite scroll
- PWA — installable on Android/iOS
- Category filtering
README

echo ""
echo "=== Done! ==="
echo "Project created in ./$PROJECT"
echo ""
echo "Next steps:"
echo "  cd $PROJECT"
echo "  ./scripts/setup.sh"
echo "  vim .env"
echo "  ./scripts/run.sh"
echo ""
echo "To push to GitHub:"
echo "  cd $PROJECT"
echo "  git init && git add -A"
echo "  git commit -m 'feat: initial cBubble'"
echo "  git remote add origin git@github.com:YOUR_USER/cbubble.git"
echo "  git push -u origin main"
