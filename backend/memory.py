"""Signal memory — dedup, persistence, competitor tracking.

Primary store: local JSON file (demo-safe, zero infra).
Interface is Senso.ai-compatible so the backend can be swapped.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DATA_DIR = Path(os.environ.get("SCOUT_DATA_DIR", "data"))
_MEMORY_FILE = _DATA_DIR / "memory.json"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load() -> dict[str, Any]:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    if _MEMORY_FILE.exists():
        try:
            return json.loads(_MEMORY_FILE.read_text())
        except Exception:
            logger.warning("memory: corrupt file, resetting")
    return {"signals": {}, "seen_hashes": [], "competitors": {}}


def _persist(data: dict[str, Any]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _MEMORY_FILE.write_text(json.dumps(data, indent=2, default=str))


def _content_hash(signal: dict) -> str:
    key = (
        f"{signal.get('competitor', '')}:"
        f"{signal.get('type', '')}:"
        f"{signal.get('summary', '')[:120]}"
    )
    return hashlib.sha256(key.encode()).hexdigest()[:20]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def save_signals(competitor: str, signals: list[dict]) -> list[dict]:
    """Persist *signals* for *competitor*, deduplicating against history.

    Returns only the net-new signals (unseen since last run).
    """
    data = _load()
    seen: set[str] = set(data.get("seen_hashes", []))
    stored: list[dict] = data["signals"].get(competitor, [])
    new_signals: list[dict] = []

    for signal in signals:
        h = _content_hash(signal)
        if h not in seen:
            seen.add(h)
            stored.append(signal)
            new_signals.append(signal)

    data["signals"][competitor] = stored[-500:]       # keep last 500 per competitor
    data["seen_hashes"] = list(seen)[-10_000:]        # keep last 10k hashes
    _persist(data)
    logger.info(
        "save_signals: %d new / %d total for %r",
        len(new_signals),
        len(stored),
        competitor,
    )
    return new_signals


async def load_signals(competitor: str, limit: int = 50) -> list[dict]:
    """Retrieve stored signals for *competitor* (most recent first)."""
    data = _load()
    signals = data["signals"].get(competitor, [])
    return list(reversed(signals[-limit:]))


async def load_all_signals(company: str, limit: int = 200) -> list[dict]:
    """Retrieve signals across all tracked competitors of *company*."""
    data = _load()
    competitors = data["competitors"].get(company.lower(), [])
    all_signals: list[dict] = []
    for competitor in competitors:
        all_signals.extend(data["signals"].get(competitor, []))
    all_signals.sort(key=lambda s: s.get("detected_at", ""), reverse=True)
    return all_signals[:limit]


async def save_competitors(company: str, competitors: list[str]) -> None:
    """Persist the competitor list for *company*."""
    data = _load()
    data["competitors"][company.lower()] = competitors
    _persist(data)


async def load_competitors(company: str) -> list[str]:
    """Load the cached competitor list for *company*."""
    data = _load()
    return data["competitors"].get(company.lower(), [])
