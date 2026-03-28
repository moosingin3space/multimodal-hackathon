"""Auto-discover competitors from a company name via DigitalOcean Gradient inference."""
from __future__ import annotations

import json
import logging
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pre-seeded competitor map — instant response for demo + popular companies
# ---------------------------------------------------------------------------
_KNOWN_COMPETITORS: dict[str, list[str]] = {
    "cisco": [
        "Juniper Networks",
        "Palo Alto Networks",
        "Fortinet",
        "Arista Networks",
        "Check Point Software",
        "CrowdStrike",
        "Zscaler",
    ],
    "palo alto networks": [
        "Cisco",
        "Fortinet",
        "Check Point Software",
        "CrowdStrike",
        "Zscaler",
        "SentinelOne",
    ],
    "fortinet": [
        "Cisco",
        "Palo Alto Networks",
        "Check Point Software",
        "SonicWall",
        "Sophos",
        "CrowdStrike",
    ],
    "apple": ["Samsung", "Google", "Microsoft", "Meta", "Amazon", "Huawei"],
    "google": ["Microsoft", "Apple", "Meta", "Amazon", "Baidu", "Alibaba"],
    "microsoft": ["Google", "Apple", "Amazon", "Oracle", "Salesforce", "IBM"],
    "amazon": ["Microsoft", "Google", "Alibaba", "Shopify", "Walmart"],
    "salesforce": [
        "Microsoft Dynamics",
        "Oracle",
        "HubSpot",
        "SAP",
        "Zoho",
        "ServiceNow",
    ],
    "stripe": [
        "Square",
        "PayPal",
        "Braintree",
        "Adyen",
        "Checkout.com",
        "Plaid",
    ],
    "openai": [
        "Anthropic",
        "Google DeepMind",
        "Meta AI",
        "Mistral AI",
        "Cohere",
        "Stability AI",
    ],
}

_SYSTEM_PROMPT = (
    "You are a competitive intelligence expert. "
    "When given a company name, list its 6-8 most direct competitors in the same market segment. "
    "Return ONLY a valid JSON array of company name strings with no explanation or markdown. "
    'Example: ["Competitor A", "Competitor B", "Competitor C"]'
)


def _make_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="openai-gpt-oss-120b",
        openai_api_base="https://inference.do-ai.run/v1",
        openai_api_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY", "placeholder"),
        temperature=0,
        max_tokens=256,
    )


async def discover_competitors(company_name: str) -> list[str]:
    """Return a list of competitor names for *company_name*.

    Priority order:
    1. Pre-seeded map (instant, demo-safe)
    2. Gradient LLM inference
    3. Stub fallback
    """
    key = company_name.lower().strip()

    if key in _KNOWN_COMPETITORS:
        logger.info("discover_competitors: cache hit for %r", company_name)
        return _KNOWN_COMPETITORS[key]

    api_key = os.environ.get("GRADIENT_MODEL_ACCESS_KEY", "")
    if not api_key:
        logger.warning("GRADIENT_MODEL_ACCESS_KEY not set — returning stub competitors")
        return [f"{company_name} Competitor {i}" for i in range(1, 6)]

    try:
        llm = _make_llm()
        response = await llm.ainvoke(
            [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=f"Company: {company_name}"),
            ]
        )
        text = response.content.strip()
        # Handle markdown code fences and bare JSON arrays
        match = re.search(r"\[.*?\]", text, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            if isinstance(parsed, list) and parsed:
                return [str(c).strip() for c in parsed[:8] if c]
    except Exception:
        logger.exception("discover_competitors: LLM call failed for %r", company_name)

    return [f"{company_name} Competitor {i}" for i in range(1, 6)]
