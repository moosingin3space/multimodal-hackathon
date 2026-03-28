"""Railtracks autonomous scheduler — runs the agent loop 24/7 every 30 minutes.

Can be started standalone:
    python -m backend.scheduler cisco

Or triggered from the FastAPI startup hook.
"""
from __future__ import annotations

import asyncio
import logging
import sys

from backend.agent import run_agent
from backend.daily_report import generate_daily_report

logger = logging.getLogger(__name__)

_DEFAULT_INTERVAL = 1800  # 30 minutes


async def run_forever(company_name: str, interval_seconds: int = _DEFAULT_INTERVAL) -> None:
    """Poll indefinitely, running a full intelligence sweep every *interval_seconds*."""
    logger.info(
        "Scheduler started for %r — sweep every %ds", company_name, interval_seconds
    )
    while True:
        try:
            result = await run_agent(company_name)
            logger.info(
                "Sweep complete: %d new signals across %d competitors",
                result.get("new_signals", 0),
                result.get("competitors_swept", 0),
            )
        except Exception:
            logger.exception("Scheduler sweep failed")
        await asyncio.sleep(interval_seconds)


async def run_daily_report(company_name: str) -> dict:
    """Trigger the end-of-day report (call from a cron job at 5PM)."""
    logger.info("Generating daily report for %r", company_name)
    return await generate_daily_report(company_name)


if __name__ == "__main__":
    company = sys.argv[1] if len(sys.argv) > 1 else "cisco"
    asyncio.run(run_forever(company))
