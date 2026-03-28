"""Analyze images using Gemini 2.0 Flash — job posting screenshots, news thumbnails, charts."""
from __future__ import annotations

import asyncio
import base64
import logging
import os
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 20.0
_MAX_IMAGES = 5


async def analyze_images(competitor: str, image_urls: list[str] | None = None) -> list[dict]:
    """Return Gemini image analysis results for *competitor*.

    If *image_urls* is not provided, no images are analyzed (caller should
    pass URLs discovered by other workers).
    """
    if not image_urls:
        return []

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("analyze_images: GEMINI_API_KEY not set — skipping image analysis")
        return []

    tasks = [_analyze_one(url, competitor, api_key) for url in image_urls[:_MAX_IMAGES]]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    analyses: list[dict] = []
    for r in results:
        if isinstance(r, dict):
            analyses.append(r)
        elif isinstance(r, Exception):
            logger.debug("analyze_images: task error: %s", r)

    logger.info("analyze_images: %d analyses for %r", len(analyses), competitor)
    return analyses


async def _analyze_one(image_url: str, competitor: str, api_key: str) -> dict:
    """Fetch *image_url* and ask Gemini to extract competitive signals from it."""
    image_data = await _fetch_image(image_url)
    if not image_data:
        raise ValueError(f"Could not fetch image: {image_url}")

    mime = _guess_mime(image_url)
    b64 = base64.b64encode(image_data).decode()

    prompt = (
        f"You are analyzing a screenshot or image related to {competitor}. "
        "Extract any competitive intelligence signals visible in this image. "
        "Look for: product features, pricing, job titles, hiring patterns, partnerships, "
        "revenue indicators, or strategic announcements. "
        "Respond in JSON with keys: signals (list of strings), sentiment (positive/neutral/negative), "
        "key_finding (one sentence summary), confidence (0-1)."
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"inline_data": {"mime_type": mime, "data": b64}},
                    {"text": prompt},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"]

    # Try to parse JSON from Gemini response
    import json
    import re
    match = re.search(r"\{.*\}", text, re.DOTALL)
    parsed: dict = {}
    if match:
        try:
            parsed = json.loads(match.group())
        except Exception:
            pass

    return {
        "image_url": image_url,
        "competitor": competitor,
        "signals": parsed.get("signals", []),
        "sentiment": parsed.get("sentiment", "neutral"),
        "key_finding": parsed.get("key_finding", text[:200]),
        "confidence": parsed.get("confidence", 0.7),
        "raw_text": text[:500],
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


async def _fetch_image(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "ScoutAgent/1.0"})
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
                return resp.content
    except Exception:
        pass
    return None


def _guess_mime(url: str) -> str:
    url_lower = url.lower()
    if url_lower.endswith(".png"):
        return "image/png"
    if url_lower.endswith(".gif"):
        return "image/gif"
    if url_lower.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"
