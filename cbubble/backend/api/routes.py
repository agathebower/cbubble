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
