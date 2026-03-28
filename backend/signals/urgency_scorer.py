"""Score urgency and decide whether to surface a signal immediately or hold for daily report."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Urgency levels: low < medium < high < critical
# ---------------------------------------------------------------------------

_URGENCY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
_URGENCY_FROM_RANK = {v: k for k, v in _URGENCY_RANK.items()}

# Base urgency by signal type
_BASE_URGENCY: dict[str, str] = {
    # Employee signals
    "product_launch": "high",
    "pricing_change": "critical",
    "hiring_surge": "high",
    "partnership": "medium",
    "exec_move": "high",
    "reorg": "medium",
    # Investor signals
    "funding": "critical",
    "revenue_proxy": "medium",
    "growth_indicator": "medium",
    "red_flag": "critical",
    "market_expansion": "high",
    "talent_velocity": "medium",
    # Default
    "github_activity": "low",
    "other": "low",
}

# surface_now threshold: urgency >= this triggers immediate push
_SURFACE_NOW_MIN = "high"


async def score_urgency(signal: dict) -> dict:
    """Attach an urgency score and surface_now flag to *signal*."""
    sig_type = signal.get("type", "other")
    base = _BASE_URGENCY.get(sig_type, "low")
    rank = _URGENCY_RANK[base]

    # Boost: very recent signals (< 4 hours)
    detected_at = signal.get("detected_at", "")
    age_hours = _age_hours(detected_at)
    if age_hours < 4:
        rank = min(3, rank + 1)
    elif age_hours > 168:  # > 7 days, demote
        rank = max(0, rank - 1)

    # Boost: investor signals with large momentum delta
    momentum_delta = signal.get("momentum_delta", 0)
    if abs(momentum_delta) >= 8:
        rank = min(3, rank + 1)

    urgency = _URGENCY_FROM_RANK[rank]
    surface_now = _URGENCY_RANK[urgency] >= _URGENCY_RANK[_SURFACE_NOW_MIN]

    return {
        **signal,
        "urgency": urgency,
        "surface_now": surface_now,
    }


def _age_hours(detected_at: str) -> float:
    """Return how many hours ago *detected_at* was."""
    if not detected_at:
        return 0.0
    try:
        dt = datetime.fromisoformat(detected_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return delta.total_seconds() / 3600
    except Exception:
        return 0.0
