"""Senso.ai memory layer — dedup, signal history, and learning."""


async def save_signals(competitor: str, signals: list[dict]) -> None:
    """Persist *signals* for *competitor*, deduplicating against history."""
    # TODO: integrate Senso.ai SDK
    raise NotImplementedError


async def load_signals(competitor: str) -> list[dict]:
    """Retrieve stored signals for *competitor*."""
    # TODO: integrate Senso.ai SDK
    raise NotImplementedError
