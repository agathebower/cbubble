"""Background worker for generating abstracts."""

import asyncio
import logging
from ..database import get_pending_stories, update_abstract, reset_errored_abstracts
from ..abstracts.engine import AbstractEngine
from ..config import load_config
from ..notify import telegram_notify

log = logging.getLogger("cbubble.worker.abstract")


async def process_pending(engine: AbstractEngine, batch_size=5):
    await reset_errored_abstracts()
    stories = await get_pending_stories(limit=batch_size)
    if not stories:
        return 0
    log.info("Processing %d pending abstracts", len(stories))
    config = load_config()
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
            if config.notify_keywords and result["status"] in ("verified", "flagged"):
                title_lower = story["title"].lower()
                matched = [kw for kw in config.notify_keywords if kw.lower() in title_lower]
                if matched:
                    await telegram_notify(
                        f"🔔 cbubble: keyword match [{', '.join(matched)}]\n{story['title']}"
                    )
            safe_title = story["title"].replace("\n", "\\n").replace("\r", "\\r")[:50]
            log.info("Abstract for '%s': %s (provider: %s)",
                     safe_title, result["status"], result["provider"])
        except Exception as e:
            safe_err = str(e).replace("\n", "\\n").replace("\r", "\\r")[:200]
            log.error("Failed abstract for story %d: %s", story["id"], safe_err)
            await update_abstract(story["id"], "", "error", str(e))
        await asyncio.sleep(2)
    return processed
