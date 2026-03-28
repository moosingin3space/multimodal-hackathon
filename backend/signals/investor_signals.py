"""Extract investor-relevant signals: revenue proxies, momentum, funding, red flags."""
from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

_SIGNAL_TYPES = [
    "funding",
    "revenue_proxy",
    "growth_indicator",
    "red_flag",
    "market_expansion",
    "talent_velocity",
    "other",
]

_SYSTEM = """You are a financial analyst and VC investor monitoring a company for investment signals.

Given raw data (news, job postings, web content, GitHub activity), extract signals relevant to investors:
- funding: Funding round, IPO filing, secondary sale, valuation news
- revenue_proxy: Customer wins, enterprise contracts, partnership deal value, user growth mentions
- growth_indicator: International expansion, new verticals, product-led growth signals
- red_flag: Layoffs, executive departures, product cancellations, regulatory issues, customer churn
- market_expansion: Entering a new market, geography, or segment
- talent_velocity: Engineering headcount growth rate (leading indicator of product investment)

Return a JSON array. Each signal must have:
{
  "type": "<type from list above>",
  "summary": "<1-2 sentence description>",
  "source_url": "<URL if available, else null>",
  "momentum_delta": <integer -10 to +10, impact on momentum score>,
  "evidence": "<direct quote or data point>"
}

Return [] if no significant signals. Return ONLY the JSON array."""


def _make_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="openai-gpt-oss-120b",
        openai_api_base="https://inference.do-ai.run/v1",
        openai_api_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY", "placeholder"),
        temperature=0.1,
        max_tokens=1024,
    )


async def extract_investor_signals(raw: dict) -> list[dict]:
    """Derive investor-relevant signals from *raw* worker output."""
    competitor = raw.get("competitor", "unknown")

    context_parts: list[str] = []

    for article in (raw.get("news") or [])[:8]:
        context_parts.append(
            f"[NEWS] {article.get('title', '')} — {article.get('summary', '')[:200]} "
            f"(url: {article.get('url', '')})"
        )

    for job in (raw.get("jobs") or [])[:15]:
        context_parts.append(
            f"[JOB POSTING] {job.get('title', '')} — dept: {job.get('department', 'unknown')}"
        )

    job_count = len(raw.get("jobs") or [])
    if job_count > 0:
        context_parts.append(f"[HIRING VOLUME] {job_count} open positions found this scan")

    for page in (raw.get("web") or [])[:5]:
        context_parts.append(
            f"[WEB] {page.get('title', '')} — {page.get('content', '')[:300]} "
            f"(url: {page.get('url', '')})"
        )

    gh_repos = raw.get("github") or []
    if gh_repos:
        total_commits = sum(r.get("commits_30d", 0) for r in gh_repos)
        total_stars = sum(r.get("stars", 0) for r in gh_repos)
        context_parts.append(
            f"[GITHUB AGGREGATE] {len(gh_repos)} active repos, "
            f"{total_commits} commits in 30d, {total_stars} total stars"
        )

    if not context_parts:
        return []

    content = f"Company being analyzed: {competitor}\n\n" + "\n".join(context_parts)

    if not os.environ.get("GRADIENT_MODEL_ACCESS_KEY"):
        return []

    try:
        llm = _make_llm()
        response = await llm.ainvoke(
            [SystemMessage(content=_SYSTEM), HumanMessage(content=content)]
        )
        text = response.content.strip()
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        raw_signals = json.loads(match.group())
    except Exception:
        logger.exception("extract_investor_signals: LLM failed for %r", competitor)
        return []

    now = datetime.now(timezone.utc).isoformat()
    signals: list[dict] = []
    for s in raw_signals:
        if not isinstance(s, dict):
            continue
        sig_type = s.get("type", "other")
        if sig_type not in _SIGNAL_TYPES:
            sig_type = "other"
        signals.append(
            {
                "id": str(uuid.uuid4()),
                "competitor": competitor,
                "type": sig_type,
                "summary": s.get("summary", "")[:300],
                "urgency": "medium",
                "surface_now": False,
                "detected_at": now,
                "source_url": s.get("source_url"),
                "image_url": None,
                "gemini_analysis": None,
                "mode": "investor",
                "momentum_delta": max(-10, min(10, int(s.get("momentum_delta", 0)))),
                "evidence": s.get("evidence", "")[:200],
            }
        )

    logger.info(
        "extract_investor_signals: %d signals for %r", len(signals), competitor
    )
    return signals
