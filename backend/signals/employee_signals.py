"""Extract employee-observable signals: product launches, pricing, hiring, partnerships, exec moves."""
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
    "product_launch",
    "pricing_change",
    "hiring_surge",
    "partnership",
    "exec_move",
    "reorg",
    "other",
]

_SYSTEM = """You are a competitive intelligence analyst watching a competitor for an employee of their rival.

Given raw data (news, job postings, web content, GitHub activity), extract competitive signals an employee would care about:
- product_launch: New product, feature, or service announced
- pricing_change: Price increase, decrease, new tier, or promotional pricing
- hiring_surge: Unusual increase in job postings, especially in specific teams
- partnership: New partnership, integration, or acquisition
- exec_move: C-suite or VP hire, departure, or title change
- reorg: Organizational restructuring, team expansion/contraction

Return a JSON array. Each signal must have:
{
  "type": "<type from list above>",
  "summary": "<1-2 sentence description>",
  "source_url": "<URL if available, else null>",
  "image_url": "<image URL if applicable, else null>",
  "evidence": "<direct quote or data point from source>"
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


async def extract_employee_signals(raw: dict) -> list[dict]:
    """Derive employee-observable signals from *raw* worker output."""
    competitor = raw.get("competitor", "unknown")

    # Build context from all workers
    context_parts: list[str] = []

    for article in (raw.get("news") or [])[:8]:
        context_parts.append(
            f"[NEWS] {article.get('title', '')} — {article.get('summary', '')[:200]} "
            f"(source: {article.get('source', '')}, url: {article.get('url', '')})"
        )

    for job in (raw.get("jobs") or [])[:10]:
        context_parts.append(
            f"[JOB] {job.get('title', '')} at {job.get('company', '')} "
            f"— {job.get('department', '')} {job.get('location', '')} "
            f"(url: {job.get('url', '')})"
        )

    for page in (raw.get("web") or [])[:5]:
        context_parts.append(
            f"[WEB] {page.get('title', '')} — {page.get('content', '')[:300]} "
            f"(url: {page.get('url', '')})"
        )

    for repo in (raw.get("github") or [])[:5]:
        if repo.get("is_new"):
            context_parts.append(
                f"[GITHUB NEW REPO] {repo.get('full_name', '')} — {repo.get('description', '')} "
                f"({repo.get('stars', 0)} stars, {repo.get('commits_30d', 0)} commits/30d)"
            )
        elif repo.get("commits_30d", 0) > 50:
            context_parts.append(
                f"[GITHUB ACTIVE] {repo.get('full_name', '')} — {repo.get('description', '')} "
                f"({repo.get('commits_30d', 0)} commits in 30d, {repo.get('contributors', 0)} contributors)"
            )

    for img in (raw.get("images") or [])[:3]:
        context_parts.append(
            f"[IMAGE ANALYSIS] {img.get('key_finding', '')} "
            f"signals: {', '.join(img.get('signals', []))}"
        )

    if not context_parts:
        return []

    content = f"Company being watched: {competitor}\n\n" + "\n".join(context_parts)

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
        logger.exception("extract_employee_signals: LLM failed for %r", competitor)
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
                "urgency": "medium",  # scored later by urgency_scorer
                "surface_now": False,
                "detected_at": now,
                "source_url": s.get("source_url"),
                "image_url": s.get("image_url"),
                "gemini_analysis": None,
                "mode": "employee",
                "evidence": s.get("evidence", "")[:200],
            }
        )

    logger.info(
        "extract_employee_signals: %d signals for %r", len(signals), competitor
    )
    return signals
