"""Watch Google News, TechCrunch, and Reuters for competitor mentions via RSS."""
from __future__ import annotations

import logging
import urllib.parse
from datetime import datetime, timezone

import feedparser
import httpx

logger = logging.getLogger(__name__)

_FEEDS = [
    "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en",
    "https://feeds.feedburner.com/TechCrunch",
]

_TIMEOUT = 10.0


async def watch_news(competitor: str) -> list[dict]:
    """Return recent news articles mentioning *competitor*."""
    q = urllib.parse.quote(f'"{competitor}" company')
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "ScoutAgent/1.0"})
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
    except Exception:
        logger.exception("watch_news: fetch failed for %r", competitor)
        return []

    articles: list[dict] = []
    for entry in feed.entries[:15]:
        published = _parse_date(getattr(entry, "published", None))
        articles.append(
            {
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "published": published,
                "source": _extract_source(entry),
                "summary": entry.get("summary", "")[:500],
                "competitor": competitor,
            }
        )

    logger.info("watch_news: %d articles for %r", len(articles), competitor)
    return articles


def _parse_date(raw: str | None) -> str:
    if not raw:
        return datetime.now(timezone.utc).isoformat()
    try:
        import email.utils
        parsed = email.utils.parsedate_to_datetime(raw)
        return parsed.isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _extract_source(entry) -> str:
    # Google News wraps source in <source> tag
    if hasattr(entry, "source") and hasattr(entry.source, "title"):
        return entry.source.title
    if hasattr(entry, "tags") and entry.tags:
        return entry.tags[0].get("term", "")
    return "news"
