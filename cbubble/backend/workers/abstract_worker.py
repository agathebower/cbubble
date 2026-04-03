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
