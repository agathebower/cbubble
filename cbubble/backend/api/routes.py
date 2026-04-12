"""REST API routes."""

from enum import Enum

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_stories, get_story_detail, get_stats
from ..config import load_config
from .auth import require_api_key

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api")


class Category(str, Enum):
    cyber = "cyber"
    ai = "ai"
    dev = "dev"
    offensive = "offensive"
    threat_intel = "threat_intel"


@router.get("/stories")
@limiter.limit("60/minute")
async def list_stories(
    request: Request,
    page: int = Query(1, ge=1, le=10000),
    limit: int = Query(20, ge=1, le=100),
    category: Category | None = Query(None),
):
    stories = await get_stories(
        page=page, limit=limit,
        category=category.value if category else None,
    )
    return {"stories": stories, "page": page, "limit": limit}


@router.get("/stories/{story_id}")
@limiter.limit("120/minute")
async def story_detail(request: Request, story_id: int):
    story = await get_story_detail(story_id)
    if not story:
        raise HTTPException(404, "Story not found")
    return story


@router.get("/categories")
@limiter.limit("30/minute")
async def list_categories(request: Request):
    config = load_config()
    cats = sorted(set(s.category for s in config.sources if s.enabled))
    return {"categories": cats}


@router.get("/sources", dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
async def list_sources(request: Request):
    config = load_config()
    return {
        "sources": [
            {"name": s.name, "url": s.url, "category": s.category, "enabled": s.enabled}
            for s in config.sources
        ]
    }


@router.get("/stats")
@limiter.limit("30/minute")
async def stats_endpoint(request: Request):
    return await get_stats()


@router.post("/reload", dependencies=[Depends(require_api_key)])
@limiter.limit("5/hour")
async def reload_config(request: Request):
    load_config()
    return {"status": "ok"}
