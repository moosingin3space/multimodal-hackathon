"""DigitalOcean Gradient inference — trajectory summaries, momentum scoring, streaming chat."""
from __future__ import annotations

import logging
import os
from collections import Counter
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

_MODEL = "openai-gpt-oss-120b"
_BASE_URL = "https://inference.do-ai.run/v1"

_TRAJECTORY_SYSTEM = """You are a senior competitive intelligence analyst.
Given a list of signals about a competitor over the last 30 days, produce a concise intelligence brief.

Your brief must include:
1. trajectory: one of "accelerating" | "stable" | "declining"
2. narrative: 2-3 sentence strategic summary explaining the trajectory
3. strategic_inference: one sharp insight (e.g. "Based on 12 ML hires, Juniper is building AI network management")
4. threat_level: one of "low" | "medium" | "high" | "critical"
5. momentum_score: integer 0-100 (50 = baseline, >70 = accelerating, <30 = declining)

Return ONLY valid JSON with these exact keys."""

_CHAT_SYSTEM = """You are ScoutAgent, an AI competitive intelligence analyst.
You have access to real-time signals about competitors including hiring trends, product launches,
GitHub activity, news, and financial indicators. Answer questions concisely and with specific data.
If you reference a signal, include the source if known. Be direct and insightful."""


def _make_llm(streaming: bool = False) -> ChatOpenAI:
    return ChatOpenAI(
        model=_MODEL,
        openai_api_base=_BASE_URL,
        openai_api_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY", "placeholder"),
        temperature=0.2,
        max_tokens=1024,
        streaming=streaming,
    )


async def synthesize(competitor: str, signals: list[dict]) -> dict:
    """Summarise *signals* into a trajectory narrative for *competitor*.

    Returns a dict with trajectory, narrative, strategic_inference, threat_level, momentum_score.
    """
    if not signals:
        return _empty_summary(competitor)

    if not os.environ.get("GRADIENT_MODEL_ACCESS_KEY"):
        return _stub_summary(competitor, signals)

    # Build signal digest
    lines: list[str] = []
    for s in signals[-30:]:  # last 30 signals
        lines.append(
            f"- [{s.get('type', 'other').upper()}] {s.get('summary', '')} "
            f"(urgency: {s.get('urgency', 'low')}, mode: {s.get('mode', 'both')})"
        )

    content = f"Competitor: {competitor}\nSignals from last 30 days:\n" + "\n".join(lines)

    try:
        import json
        import re
        llm = _make_llm()
        response = await llm.ainvoke(
            [SystemMessage(content=_TRAJECTORY_SYSTEM), HumanMessage(content=content)]
        )
        text = response.content.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            result = json.loads(match.group())
            return {
                "competitor": competitor,
                "trajectory": result.get("trajectory", "stable"),
                "narrative": result.get("narrative", ""),
                "strategic_inference": result.get("strategic_inference", ""),
                "threat_level": result.get("threat_level", "medium"),
                "momentum_score": max(0, min(100, int(result.get("momentum_score", 50)))),
            }
    except Exception:
        logger.exception("synthesize: LLM failed for %r", competitor)

    return _stub_summary(competitor, signals)


async def stream_chat(
    prompt: str, context_signals: list[dict] | None = None
) -> AsyncGenerator[str, None]:
    """Stream a chat response from Gradient inference, optionally grounded in *context_signals*."""
    system_content = _CHAT_SYSTEM
    if context_signals:
        recent = context_signals[:20]
        signal_context = "\n".join(
            f"- [{s.get('competitor', '')} / {s.get('type', '')}] {s.get('summary', '')}"
            for s in recent
        )
        system_content += f"\n\nRecent signals in your knowledge base:\n{signal_context}"

    if not os.environ.get("GRADIENT_MODEL_ACCESS_KEY"):
        # Dev fallback: echo response
        yield f"data: ScoutAgent (dev mode): {prompt}\n\n"
        return

    try:
        llm = _make_llm(streaming=True)
        async for chunk in llm.astream(
            [SystemMessage(content=system_content), HumanMessage(content=prompt)]
        ):
            if chunk.content:
                yield f"data: {chunk.content}\n\n"
    except Exception:
        logger.exception("stream_chat: streaming failed")
        yield "data: [Error: inference unavailable]\n\n"


# ---------------------------------------------------------------------------
# Fallbacks
# ---------------------------------------------------------------------------

def _empty_summary(competitor: str) -> dict:
    return {
        "competitor": competitor,
        "trajectory": "stable",
        "narrative": "No signals collected yet for this competitor.",
        "strategic_inference": "Insufficient data for inference.",
        "threat_level": "low",
        "momentum_score": 50,
    }


def _stub_summary(competitor: str, signals: list[dict]) -> dict:
    """Rule-based summary when LLM is unavailable."""
    urgency_counts = Counter(s.get("urgency", "low") for s in signals)
    critical = urgency_counts.get("critical", 0)
    high = urgency_counts.get("high", 0)
    types = Counter(s.get("type", "other") for s in signals)

    if critical >= 2 or high >= 5:
        trajectory = "accelerating"
        threat = "high"
        score = 72
    elif critical == 0 and high <= 1:
        trajectory = "declining"
        threat = "low"
        score = 35
    else:
        trajectory = "stable"
        threat = "medium"
        score = 52

    top_type = types.most_common(1)[0][0] if types else "unknown"
    return {
        "competitor": competitor,
        "trajectory": trajectory,
        "narrative": (
            f"{competitor} shows {len(signals)} signals in the tracking window. "
            f"Primary activity type: {top_type}. "
            f"{critical} critical and {high} high-urgency signals detected."
        ),
        "strategic_inference": f"Activity pattern suggests focus on {top_type.replace('_', ' ')} initiatives.",
        "threat_level": threat,
        "momentum_score": score,
    }
