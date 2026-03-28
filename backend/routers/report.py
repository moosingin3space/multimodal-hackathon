"""GET /api/report — daily intelligence report."""
from fastapi import APIRouter, Depends, Query

from backend.auth import require_api_key
from backend.daily_report import generate_daily_report
from backend.synthesizer import synthesize
from backend.memory import load_signals

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/report")
async def get_report(company: str = Query(...)) -> dict:
    """Generate and return the daily intelligence report for *company*."""
    return await generate_daily_report(company)


@router.get("/report/competitor/{name}")
async def get_competitor_report(name: str) -> dict:
    """Return a trajectory summary for a single competitor."""
    signals = await load_signals(name, limit=100)
    return await synthesize(name, signals)
