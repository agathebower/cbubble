"""SQLite database setup and access layer."""

import aiosqlite
import logging
import os
from pathlib import Path
from datetime import datetime, timezone

log = logging.getLogger("cbubble.db")

DB_PATH = Path(os.environ.get("CBUBBLE_DB_PATH", Path(__file__).resolve().parent.parent / "cbubble.db"))

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
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    provider TEXT NOT NULL,
    call_type TEXT NOT NULL,
    model TEXT,
    success INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_llm_calls_ts ON llm_calls(ts DESC);
"""


async def init_db():
    # Ensure the DB file is created with restrictive permissions (owner read/write only)
    DB_PATH.touch(mode=0o600, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        try:
            await db.execute("ALTER TABLE stories ADD COLUMN priority INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
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
                   ORDER BY COALESCE(published_at, fetched_at) DESC LIMIT ? OFFSET ?""",
                (category, limit, offset),
            )
        else:
            rows = await db.execute_fetchall(
                """SELECT id, source_name, category, title, url, image_url,
                          published_at, fetched_at, abstract, abstract_status
                   FROM stories ORDER BY COALESCE(published_at, fetched_at) DESC LIMIT ? OFFSET ?""",
                (limit, offset),
            )
        return [dict(r) for r in rows]


async def get_pending_stories(limit=10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            """SELECT id, title, url, content_raw FROM stories
               WHERE abstract_status = 'pending' AND content_raw IS NOT NULL
               ORDER BY priority DESC, fetched_at DESC LIMIT ?""", (limit,),
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


async def prioritize_story(story_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """UPDATE stories SET abstract_status = 'pending', abstract = '',
               verification_note = NULL, priority = 1
               WHERE id = ? AND abstract_status IN ('pending', 'skipped')""",
            (story_id,),
        )
        await db.commit()
        return cursor.rowcount > 0


async def reprocess_story(story_id: int) -> bool:
    """Reset a story's abstract so the worker picks it up again, regardless of current status."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """UPDATE stories SET abstract = NULL, abstract_status = 'pending',
               verification_note = NULL, provider_used = NULL, priority = 1
               WHERE id = ?""",
            (story_id,),
        )
        await db.commit()
        return cursor.rowcount > 0


async def reset_errored_abstracts() -> int:
    """Reset 'error' stories back to 'pending' so they get retried."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE stories SET abstract_status = 'pending', abstract = '', "
            "verification_note = NULL, provider_used = NULL "
            "WHERE abstract_status = 'error'"
        )
        await db.commit()
        count = cursor.rowcount
        if count:
            log.info("Reset %d errored stories back to pending", count)
        return count


async def get_stories_without_images(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT id, url FROM stories WHERE image_url IS NULL ORDER BY fetched_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in rows]


async def update_story_image(story_id: int, image_url: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE stories SET image_url = ? WHERE id = ?", (image_url, story_id))
        await db.commit()


async def log_llm_call(provider: str, call_type: str, model: str | None, success: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO llm_calls (ts, provider, call_type, model, success) VALUES (?, ?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), provider, call_type, model, int(success)),
        )
        await db.commit()


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        total = (await db.execute_fetchall("SELECT COUNT(*) as c FROM stories"))[0]["c"]
        by_status = await db.execute_fetchall(
            "SELECT abstract_status, COUNT(*) as c FROM stories GROUP BY abstract_status"
        )
        by_category = await db.execute_fetchall(
            "SELECT category, COUNT(*) as c FROM stories GROUP BY category ORDER BY c DESC"
        )
        latest = (await db.execute_fetchall("SELECT MAX(fetched_at) as t FROM stories"))[0]["t"]
        llm_24h = (await db.execute_fetchall(
            "SELECT COUNT(*) as c FROM llm_calls WHERE ts > datetime('now', '-1 day')"
        ))[0]["c"]
        llm_7d = (await db.execute_fetchall(
            "SELECT COUNT(*) as c FROM llm_calls WHERE ts > datetime('now', '-7 days')"
        ))[0]["c"]
        llm_by_day = await db.execute_fetchall(
            """SELECT date(ts) as day, COUNT(*) as c
               FROM llm_calls GROUP BY day ORDER BY day DESC LIMIT 14"""
        )
    return {
        "total": total,
        "by_status": {r["abstract_status"]: r["c"] for r in by_status},
        "by_category": {r["category"]: r["c"] for r in by_category},
        "latest_fetch": latest,
        "llm": {
            "calls_24h": llm_24h,
            "calls_7d": llm_7d,
            "by_day": {r["day"]: r["c"] for r in llm_by_day},
        },
    }


async def get_story_detail(story_id) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await db.execute_fetchall(
            "SELECT * FROM stories WHERE id = ?", (story_id,)
        )
        return dict(row[0]) if row else None


async def migrate_published_at_to_iso() -> int:
    """One-time migration: convert RFC 2822 published_at strings to ISO 8601.

    Existing stories stored with raw RSS date strings (e.g. 'Sun, 26 Apr 2026 ...')
    sort alphabetically by weekday name, not by date. This converts them all to
    ISO 8601 so SQLite TEXT sort works correctly.
    """
    from email.utils import parsedate_to_datetime
    from datetime import timezone
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT id, published_at FROM stories "
            "WHERE published_at IS NOT NULL AND published_at NOT LIKE '____-__-__%'"
        )
        count = 0
        for row in rows:
            try:
                dt = parsedate_to_datetime(row["published_at"])
                iso = dt.astimezone(timezone.utc).isoformat()
                await db.execute(
                    "UPDATE stories SET published_at = ? WHERE id = ?",
                    (iso, row["id"]),
                )
                count += 1
            except Exception:
                pass
        if count:
            await db.commit()
            log.info("Migrated %d stories: published_at → ISO 8601", count)
        return count


async def prune_old_stories(max_age_days: int = 7) -> int:
    """Delete stories fetched more than max_age_days ago."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM stories WHERE fetched_at < datetime('now', ?)",
            (f"-{max_age_days} days",),
        )
        await db.commit()
        count = cursor.rowcount
        if count:
            log.info("Pruned %d stories older than %d days", count, max_age_days)
        return count
