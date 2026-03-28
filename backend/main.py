"""FastAPI application — ScoutAgent backend."""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import agent, chat, discover, signals, report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ScoutAgent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.environ.get("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(discover.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(signals.router, prefix="/api")
app.include_router(report.router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "ScoutAgent"}


@app.on_event("startup")
async def seed_demo_data() -> None:
    """Auto-seed Cisco demo data on startup so the dashboard has content immediately."""
    try:
        from backend.memory import load_competitors
        existing = await load_competitors("cisco")
        if not existing:
            from backend.seed_data import seed_cisco
            logger.info("Seeding Cisco demo data...")
            await seed_cisco()
            logger.info("Demo data ready.")
        else:
            logger.info("Demo data already present (%d competitors).", len(existing))
    except Exception:
        logger.exception("Failed to seed demo data — continuing without it")
