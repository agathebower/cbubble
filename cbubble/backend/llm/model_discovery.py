"""Cerebras model discovery — fetches available models and picks the best one."""

import httpx
import logging
import time

log = logging.getLogger("cbubble.llm.discovery")

CEREBRAS_MODELS_URL = "https://api.cerebras.ai/v1/models"

# Preference order: first match wins. Each entry is a substring to match in model ID.
MODEL_PREFERENCES = ["qwen", "llama", "glm", "gpt"]

_cache: dict = {"model": None, "models": [], "updated_at": 0.0}


async def fetch_available_models(api_key: str) -> list[str]:
    """Fetch the list of available model IDs from Cerebras."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(CEREBRAS_MODELS_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            models = [m["id"] for m in data.get("data", [])]
            log.info("Cerebras models available: %s", models)
            return models
    except Exception as e:
        log.error("Failed to fetch Cerebras models: %s", e)
        return []


def pick_best_model(models: list[str]) -> str | None:
    """Pick the best model based on preference order."""
    for pref in MODEL_PREFERENCES:
        matches = [m for m in models if pref in m.lower()]
        if matches:
            # Among matches, prefer larger models (sort by name descending to get e.g. 235b before 8b)
            matches.sort(key=lambda m: m, reverse=True)
            return matches[0]
    # No preference matched — return the first model if any
    return models[0] if models else None


async def discover_model(api_key: str) -> str | None:
    """Fetch models and return the best one. Updates the cache."""
    models = await fetch_available_models(api_key)
    if not models:
        if _cache["model"]:
            log.warning("Model fetch failed, keeping cached model: %s", _cache["model"])
            return _cache["model"]
        return None

    best = pick_best_model(models)
    _cache["model"] = best
    _cache["models"] = models
    _cache["updated_at"] = time.time()
    log.info("Selected model: %s (from %d available)", best, len(models))
    return best


def get_cached_model() -> str | None:
    """Return the last discovered model without making an API call."""
    return _cache["model"]


def get_cached_models() -> list[str]:
    """Return the full list of cached models."""
    return _cache["models"]
