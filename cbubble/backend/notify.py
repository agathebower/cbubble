"""Telegram notification helper for cbubble backend.

Requires env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
Add these to docker-compose under cbubble service environment.
"""

import logging
import os

import httpx

log = logging.getLogger("cbubble.notify")


async def telegram_notify(message: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message},
                timeout=10,
            )
    except Exception as e:
        log.warning("Telegram notify failed: %s", e)
