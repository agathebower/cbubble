"""Periodic feed collection worker."""

import asyncio
import logging
from ..config import AppConfig, Source
from ..feeds.fetcher import fetch_rss, fetch_article_content
from ..database import insert_story, get_db, get_stories_without_images, update_story_image

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
            content, og_image = await fetch_article_content(item.url)
            if content or (og_image and not item.image_url):
                db = await get_db()
                try:
                    if content:
                        await db.execute("UPDATE stories SET content_raw = ? WHERE id = ?",
                                         (content, story_id))
                    if og_image and not item.image_url:
                        await db.execute("UPDATE stories SET image_url = ? WHERE id = ?",
                                         (og_image, story_id))
                    await db.commit()
                finally:
                    await db.close()
    if new_count:
        log.info("Source %s: %d new stories", source.name, new_count)
    return new_count


async def backfill_images(batch_size: int = 25) -> int:
    """Fetch og:image for existing stories that have no image_url."""
    stories = await get_stories_without_images(limit=batch_size)
    if not stories:
        return 0
    filled = 0
    for story in stories:
        try:
            _, og_image = await fetch_article_content(story["url"])
            if og_image:
                await update_story_image(story["id"], og_image)
                filled += 1
        except Exception as e:
            log.debug("Image backfill failed for story %d: %s", story["id"], e)
        await asyncio.sleep(1.5)
    if filled:
        log.info("Image backfill: %d/%d stories updated", filled, len(stories))
    return filled


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
