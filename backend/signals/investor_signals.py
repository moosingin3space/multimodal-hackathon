"""Extract momentum, revenue proxies, and red-flag signals."""


async def extract_investor_signals(raw: dict) -> list[dict]:
    """Derive investor-relevant signals from *raw* worker output."""
    # TODO: classify signals by type (funding, revenue proxy, churn risk, etc.)
    raise NotImplementedError
