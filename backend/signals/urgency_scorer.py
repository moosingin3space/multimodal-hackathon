"""Decide whether a signal is urgent enough to surface now vs. in the daily report."""


async def score_urgency(signal: dict) -> dict:
    """Attach an urgency score and surface flag to *signal*."""
    # TODO: score based on signal type, recency, and competitor trajectory
    raise NotImplementedError
