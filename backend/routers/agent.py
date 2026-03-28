"""Trigger an agent run against tracked competitors."""
from fastapi import APIRouter, BackgroundTasks, Depends

from backend.auth import require_api_key
from backend.agent import run_agent

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/agent/run")
async def trigger_agent(
    company_name: str, background_tasks: BackgroundTasks
) -> dict:
    background_tasks.add_task(run_agent, company_name)
    return {"status": "queued", "company": company_name}
