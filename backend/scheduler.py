"""Railtracks autonomous scheduler — runs the agent loop 24/7."""
import asyncio

from backend.agent import run_agent
from backend.daily_report import generate_daily_report


async def run_forever(company_name: str, interval_seconds: int = 3600) -> None:
    """Poll indefinitely, running an agent sweep every *interval_seconds*."""
    while True:
        await run_agent(company_name)
        await asyncio.sleep(interval_seconds)


async def run_daily_report(company_name: str) -> None:
    """Trigger the end-of-day report (call from a cron job at midnight)."""
    await generate_daily_report(company_name)
