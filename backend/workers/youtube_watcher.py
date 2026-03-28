"""Delegate YouTube search to the youtube_agent."""
from agents.youtube_agent import run


async def watch_youtube(competitor: str) -> list[dict]:
    """Return ranked YouTube videos about *competitor*."""
    return await run(competitor)
