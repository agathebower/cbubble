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
