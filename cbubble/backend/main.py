"""cBubble — Custom News Feed Aggregator."""

import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pathlib import Path

from .config import load_config
from .database import init_db
from .llm.manager import LLMManager
from .llm.model_discovery import discover_model
from .abstracts.engine import AbstractEngine
from .workers.feed_worker import collect_all
from .workers.abstract_worker import process_pending
from .api.routes import router as api_router

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger("cbubble")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

config = None
llm_manager = None
abstract_engine = None
scheduler = AsyncIOScheduler()


async def scheduled_feed_collect():
    await collect_all(config)
    await process_pending(abstract_engine, batch_size=10)


async def refresh_models():
    """Daily job: re-discover available Cerebras models and update providers."""
    if not config or not config.cerebras:
        return
    model = await discover_model(config.cerebras.abstract_api_key)
    if model and llm_manager:
        llm_manager.update_model(model)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global config, llm_manager, abstract_engine
    config = load_config()
    await init_db()

    # Discover the best available Cerebras model before initializing providers
    model = None
    if config.cerebras:
        model = await discover_model(config.cerebras.abstract_api_key)
    if not model:
        model = "qwen-3-235b-a22b-instruct-2507"  # safe fallback
        log.warning("Model discovery failed, using fallback: %s", model)

    llm_manager = LLMManager(config, model=model)
    abstract_engine = AbstractEngine(llm_manager, config.max_abstract_sentences)

    scheduler.add_job(scheduled_feed_collect, "interval",
                      minutes=config.refresh_interval_minutes,
                      id="feed_collect", replace_existing=True)
    scheduler.add_job(refresh_models, "interval", hours=24,
                      id="model_refresh", replace_existing=True)
    scheduler.start()
    log.info("Scheduler started: feeds every %d min, model refresh every 24h",
             config.refresh_interval_minutes)
    log.info("Running initial feed collection...")
    await collect_all(config)
    await process_pending(abstract_engine, batch_size=10)
    yield
    scheduler.shutdown(wait=False)
    log.info("cBubble shut down.")


app = FastAPI(title="cBubble", version="0.1.0", lifespan=lifespan)
app.include_router(api_router)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/manifest.json")
    async def serve_manifest():
        return FileResponse(FRONTEND_DIR / "manifest.json")

    @app.get("/sw.js")
    async def serve_sw():
        return FileResponse(FRONTEND_DIR / "sw.js", media_type="application/javascript")
