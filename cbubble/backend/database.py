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
