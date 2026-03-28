"""GET /api/signals — return signals for a company's competitors, with optional mode filter."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.auth import require_api_key
from backend.memory import load_all_signals, load_competitors, load_signals

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/signals")
async def get_signals(
    company: str = Query(..., description="Company name (e.g. Cisco)"),
    mode: str | None = Query(None, description="employee | investor | both"),
    competitor: str | None = Query(None, description="Filter to single competitor"),
    limit: int = Query(100, le=500),
) -> dict:
    """Return signals for all competitors of *company*, optionally filtered."""
    if competitor:
        signals = await load_signals(competitor, limit=limit)
    else:
        signals = await load_all_signals(company, limit=limit)

    if mode and mode in ("employee", "investor"):
        signals = [
            s for s in signals
            if s.get("mode") == mode or s.get("mode") == "both"
        ]

    return {
        "company": company,
        "count": len(signals),
        "signals": signals,
    }


@router.get("/signals/urgent")
async def get_urgent_signals(
    company: str = Query(...),
    limit: int = Query(20, le=100),
) -> dict:
    """Return only surface_now=True signals, newest first."""
    all_signals = await load_all_signals(company, limit=500)
    urgent = [s for s in all_signals if s.get("surface_now")]
    urgent.sort(key=lambda s: s.get("detected_at", ""), reverse=True)
    return {"company": company, "count": len(urgent), "signals": urgent[:limit]}


@router.get("/signals/competitor/{name}")
async def get_competitor_signals(
    name: str,
    limit: int = Query(50, le=200),
) -> dict:
    """Return signals for a single competitor."""
    signals = await load_signals(name, limit=limit)
    return {"competitor": name, "count": len(signals), "signals": signals}


@router.get("/competitors")
async def get_competitors(company: str = Query(...)) -> dict:
    """Return the tracked competitor list for *company*."""
    competitors = await load_competitors(company)
    return {"company": company, "competitors": competitors}
