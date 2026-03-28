"""End-of-day comprehensive report generator — runs at 5PM or on demand."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from backend.memory import load_competitors, load_signals
from backend.synthesizer import synthesize

logger = logging.getLogger(__name__)


async def generate_daily_report(company_name: str) -> dict:
    """Aggregate all signals from the last 24h and produce a structured daily report."""
    competitors = await load_competitors(company_name)
    if not competitors:
        logger.warning("generate_daily_report: no competitors found for %r", company_name)
        return _empty_report(company_name)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    competitor_summaries: list[dict] = []

    for competitor in competitors:
        all_signals = await load_signals(competitor, limit=200)

        # Filter to last 24h for the report
        recent = [
            s for s in all_signals
            if _parse_dt(s.get("detected_at", "")) >= cutoff
        ]

        # Synthesize using all available signals (not just 24h) for trajectory
        summary = await synthesize(competitor, all_signals[:50])

        # Top 3 highest-urgency recent signals
        top_signals = sorted(
            recent,
            key=lambda s: (
                {"critical": 3, "high": 2, "medium": 1, "low": 0}.get(
                    s.get("urgency", "low"), 0
                ),
                s.get("detected_at", ""),
            ),
            reverse=True,
        )[:3]

        competitor_summaries.append(
            {
                "name": competitor,
                "trajectory": summary["trajectory"],
                "momentum_score": summary["momentum_score"],
                "threat_level": summary["threat_level"],
                "narrative": summary["narrative"],
                "strategic_inference": summary["strategic_inference"],
                "top_signals": top_signals,
                "signal_count_24h": len(recent),
            }
        )

    # Sort by threat level
    threat_rank = {"critical": 3, "high": 2, "medium": 1, "low": 0}
    competitor_summaries.sort(
        key=lambda c: (threat_rank.get(c["threat_level"], 0), c["momentum_score"]),
        reverse=True,
    )

    return {
        "company": company_name,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "competitors": competitor_summaries,
        "total_signals_24h": sum(c["signal_count_24h"] for c in competitor_summaries),
    }


def _parse_dt(iso: str) -> datetime:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def _empty_report(company_name: str) -> dict:
    return {
        "company": company_name,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "competitors": [],
        "total_signals_24h": 0,
    }
