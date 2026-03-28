"""End-of-day comprehensive report generator."""
from backend.memory import load_signals
from backend.synthesizer import synthesize


async def generate_daily_report(company_name: str) -> dict:
    """Aggregate all signals from the day and produce a report."""
    # TODO: load competitor list, gather signals, call synthesize
    raise NotImplementedError
