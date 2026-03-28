"""Phase 1 — find competitors from a company name, save to memory, trigger initial sweep."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.auth import require_api_key
from backend.discovery import discover_competitors
from backend.memory import load_competitors, save_competitors

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/discover")
async def discover(
    company_name: str = Query(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> dict:
    """Discover competitors for *company_name* and save to memory.

    Returns immediately with the competitor list. Optionally queues an
    initial agent sweep in the background.
    """
    # Return cached list if we already have one
    cached = await load_competitors(company_name)
    if cached:
        return {"company": company_name, "competitors": cached, "cached": True}

    competitors = await discover_competitors(company_name)
    await save_competitors(company_name, competitors)

    # Kick off an initial sweep in the background
    background_tasks.add_task(_initial_sweep, company_name)

    return {"company": company_name, "competitors": competitors, "cached": False}


async def _initial_sweep(company_name: str) -> None:
    """Run first agent sweep after discovery — fires once in background."""
    try:
        from backend.agent import run_agent
        await run_agent(company_name)
    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "_initial_sweep: failed for %r", company_name
        )
