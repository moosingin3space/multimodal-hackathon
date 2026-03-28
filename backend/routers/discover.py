"""Phase 1 — find competitors from a company name."""
from fastapi import APIRouter, Depends

from backend.auth import require_api_key
from backend.discovery import discover_competitors

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/discover")
async def discover(company_name: str) -> dict:
    competitors = await discover_competitors(company_name)
    return {"competitors": competitors}
