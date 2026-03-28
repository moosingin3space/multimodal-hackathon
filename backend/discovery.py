"""Delegate competitor discovery to the competitor_agent."""
from agents.competitor_agent import run


async def discover_competitors(company_name: str) -> list[str]:
    """Return a ranked list of competitor names for *company_name*."""
    return await run(company_name)
