"""Demo seed data for Cisco — pre-populated signals for reliable hackathon demo."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from backend.memory import save_competitors, save_signals


def _ts(hours_ago: float = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


# ---------------------------------------------------------------------------
# Seeded signals — realistic competitive intelligence for Cisco demo
# ---------------------------------------------------------------------------

_PALO_ALTO_SIGNALS = [
    {
        "id": str(uuid.uuid4()),
        "competitor": "Palo Alto Networks",
        "type": "hiring_surge",
        "summary": "Palo Alto Networks posted 34 AI security engineering roles in the last 7 days — 3× their normal run rate. Roles concentrated in Precision AI and autonomous SOC divisions.",
        "urgency": "high",
        "surface_now": True,
        "detected_at": _ts(2),
        "source_url": "https://jobs.paloaltonetworks.com",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/1200px-Amazon_logo.svg.png",
        "gemini_analysis": "Job posting screenshot shows 12 ML Engineer roles targeting LLM-based threat detection, suggesting major investment in AI-native security platform.",
        "mode": "employee",
        "evidence": "34 AI engineering job postings in 7 days, departments: Precision AI (18), Autonomous SOC (9), XSIAM (7)",
        "momentum_delta": 7,
    },
    {
        "id": str(uuid.uuid4()),
        "competitor": "Palo Alto Networks",
        "type": "product_launch",
        "summary": "Palo Alto Networks launched AI-powered firewall policy recommendations in NGFW 11.2, directly targeting Cisco's Firepower customer base.",
        "urgency": "high",
        "surface_now": True,
        "detected_at": _ts(6),
        "source_url": "https://www.paloaltonetworks.com/blog",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "employee",
        "evidence": "Official product blog post announcing NGFW 11.2 with Precision AI recommendations",
        "momentum_delta": 8,
    },
    {
        "id": str(uuid.uuid4()),
        "competitor": "Palo Alto Networks",
        "type": "funding",
        "summary": "Palo Alto Networks Q2 FY25 earnings: $2.26B revenue (+14% YoY), RPO grew 22% to $12.6B signaling strong future revenue visibility.",
        "urgency": "medium",
        "surface_now": False,
        "detected_at": _ts(18),
        "source_url": "https://investors.paloaltonetworks.com",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "investor",
        "evidence": "Q2 FY25 earnings release: $2.26B revenue, $12.6B RPO",
        "momentum_delta": 6,
    },
    {
        "id": str(uuid.uuid4()),
        "competitor": "Palo Alto Networks",
        "type": "partnership",
        "summary": "Palo Alto Networks announced strategic partnership with IBM to embed Precision AI into IBM QRadar SIEM, expanding SOC platform reach.",
        "urgency": "high",
        "surface_now": True,
        "detected_at": _ts(30),
        "source_url": "https://newsroom.paloaltonetworks.com",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "employee",
        "evidence": "Joint press release from Palo Alto Networks and IBM",
        "momentum_delta": 5,
    },
]

_JUNIPER_SIGNALS = [
    {
        "id": str(uuid.uuid4()),
        "competitor": "Juniper Networks",
        "type": "red_flag",
        "summary": "Juniper Networks headcount down 8% following HPE acquisition integration — 1,200 roles eliminated across engineering and sales.",
        "urgency": "high",
        "surface_now": True,
        "detected_at": _ts(12),
        "source_url": "https://www.reuters.com",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "investor",
        "evidence": "Reuters report citing HPE post-acquisition restructuring, 1,200 layoffs confirmed",
        "momentum_delta": -9,
    },
    {
        "id": str(uuid.uuid4()),
        "competitor": "Juniper Networks",
        "type": "revenue_proxy",
        "summary": "Juniper Networks Q4 revenue declined 11% YoY to $1.26B — 3rd consecutive quarter of decline as HPE integration slows enterprise deals.",
        "urgency": "medium",
        "surface_now": False,
        "detected_at": _ts(36),
        "source_url": "https://investor.juniper.net",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "investor",
        "evidence": "Q4 earnings: $1.26B revenue vs $1.41B prior year",
        "momentum_delta": -7,
    },
    {
        "id": str(uuid.uuid4()),
        "competitor": "Juniper Networks",
        "type": "exec_move",
        "summary": "Juniper Networks CTO Raj Yavatkar departed to join Arista Networks, signaling talent drain post-HPE acquisition.",
        "urgency": "high",
        "surface_now": True,
        "detected_at": _ts(48),
        "source_url": "https://www.linkedin.com",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "employee",
        "evidence": "LinkedIn profile update confirming Arista Networks CTO role",
        "momentum_delta": -6,
    },
]

_FORTINET_SIGNALS = [
    {
        "id": str(uuid.uuid4()),
        "competitor": "Fortinet",
        "type": "product_launch",
        "summary": "Fortinet launched FortiAI 3.0 with inline AI threat prevention — targets SMB and mid-market segments where Cisco has high margins.",
        "urgency": "medium",
        "surface_now": False,
        "detected_at": _ts(24),
        "source_url": "https://www.fortinet.com/blog",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "employee",
        "evidence": "Product launch blog and press release for FortiAI 3.0",
        "momentum_delta": 4,
    },
    {
        "id": str(uuid.uuid4()),
        "competitor": "Fortinet",
        "type": "growth_indicator",
        "summary": "Fortinet OT security bookings grew 38% YoY — rapidly expanding in industrial/critical infrastructure, a Cisco stronghold.",
        "urgency": "medium",
        "surface_now": False,
        "detected_at": _ts(72),
        "source_url": "https://investor.fortinet.com",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "investor",
        "evidence": "Q3 earnings call transcript: CEO cited 38% OT bookings growth",
        "momentum_delta": 5,
    },
]

_CROWDSTRIKE_SIGNALS = [
    {
        "id": str(uuid.uuid4()),
        "competitor": "CrowdStrike",
        "type": "market_expansion",
        "summary": "CrowdStrike launched Falcon Firewall Management, entering network security — direct competition with Cisco Secure Firewall.",
        "urgency": "critical",
        "surface_now": True,
        "detected_at": _ts(4),
        "source_url": "https://www.crowdstrike.com/blog",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "employee",
        "evidence": "Falcon platform release notes and product press release",
        "momentum_delta": 9,
    },
    {
        "id": str(uuid.uuid4()),
        "competitor": "CrowdStrike",
        "type": "talent_velocity",
        "summary": "CrowdStrike engineering headcount grew 23% in 12 months — 450 new engineers hired, 60% in AI/ML roles.",
        "urgency": "medium",
        "surface_now": False,
        "detected_at": _ts(60),
        "source_url": "https://www.linkedin.com",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "investor",
        "evidence": "LinkedIn headcount data analysis across CrowdStrike engineering",
        "momentum_delta": 7,
    },
]

_ARISTA_SIGNALS = [
    {
        "id": str(uuid.uuid4()),
        "competitor": "Arista Networks",
        "type": "revenue_proxy",
        "summary": "Arista Networks data center switching revenue hit record $1.9B in Q3, growing 20% YoY — taking share in hyperscaler accounts from Cisco.",
        "urgency": "medium",
        "surface_now": False,
        "detected_at": _ts(90),
        "source_url": "https://investors.arista.com",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "investor",
        "evidence": "Q3 earnings: $1.9B data center revenue",
        "momentum_delta": 6,
    },
]

_ZSCALER_SIGNALS = [
    {
        "id": str(uuid.uuid4()),
        "competitor": "Zscaler",
        "type": "pricing_change",
        "summary": "Zscaler introduced ZIA Business Plus at $8/user/month — aggressive pricing targeting Cisco Umbrella customers with a direct migration offer.",
        "urgency": "critical",
        "surface_now": True,
        "detected_at": _ts(1),
        "source_url": "https://www.zscaler.com/pricing",
        "image_url": None,
        "gemini_analysis": None,
        "mode": "employee",
        "evidence": "Zscaler pricing page updated with new tier and explicit 'migrate from Cisco Umbrella' CTA",
        "momentum_delta": 8,
    },
]

_ALL_COMPETITOR_SIGNALS = {
    "Palo Alto Networks": _PALO_ALTO_SIGNALS,
    "Juniper Networks": _JUNIPER_SIGNALS,
    "Fortinet": _FORTINET_SIGNALS,
    "CrowdStrike": _CROWDSTRIKE_SIGNALS,
    "Arista Networks": _ARISTA_SIGNALS,
    "Zscaler": _ZSCALER_SIGNALS,
}

CISCO_COMPETITORS = [
    "Palo Alto Networks",
    "Juniper Networks",
    "Fortinet",
    "Arista Networks",
    "Check Point Software",
    "CrowdStrike",
    "Zscaler",
]


async def seed_cisco() -> None:
    """Load demo data for Cisco into memory. Idempotent — safe to call multiple times."""
    await save_competitors("cisco", CISCO_COMPETITORS)
    for competitor, signals in _ALL_COMPETITOR_SIGNALS.items():
        new = await save_signals(competitor, signals)
        print(f"  Seeded {competitor}: {len(new)} new signals")
    print("Cisco demo data seeded.")


if __name__ == "__main__":
    asyncio.run(seed_cisco())
