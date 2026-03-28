"""Watch for competitor news using Exa semantic search.

Replaces RSS scraping with Exa's neural search for higher signal quality.
Falls back to Google News RSS if EXA_API_KEY is not configured.
"""
from __future__ import annotations

import logging
import os
import urllib.parse
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

_EXA_API_KEY = os.environ.get("EXA_API_KEY")
_TIMEOUT = 10.0


async def watch_news(competitor: str, since_days: int = 7) -> list[dict]:
    """Return recent news articles mentioning *competitor*.

    Uses Exa semantic search when EXA_API_KEY is set; falls back to
    Google News RSS otherwise.
    """
    if _EXA_API_KEY:
        return await _watch_news_exa(competitor, since_days)
    return await _watch_news_rss(competitor)


# ---------------------------------------------------------------------------
# Exa path
# ---------------------------------------------------------------------------

async def _watch_news_exa(competitor: str, since_days: int) -> list[dict]:
    try:
        from exa_py import AsyncExa
    except ImportError:
        logger.warning("exa-py not installed — falling back to RSS")
        return await _watch_news_rss(competitor)

    since = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # Three queries covering distinct signal types
    queries = [
        f"{competitor} latest news announcement",
        f"{competitor} product launch partnership acquisition",
        f"{competitor} revenue earnings growth strategy",
    ]

    exa = AsyncExa(api_key=_EXA_API_KEY)
    seen_urls: set[str] = set()
    articles: list[dict] = []

    for query in queries:
        try:
            result = await exa.search(
                query,
                num_results=5,
                use_autoprompt=True,
                start_published_date=since,
                type="neural",
                category="news",
            )
            for item in result.results:
                url = item.url or ""
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                articles.append({
                    "title": item.title or "",
                    "url": url,
                    "published": item.published_date or datetime.now(timezone.utc).isoformat(),
                    "source": _domain(url),
                    "summary": (getattr(item, "text", None) or "")[:600],
                    "competitor": competitor,
                    "exa_score": getattr(item, "score", None),
                })
        except Exception:
            logger.exception(
                "_watch_news_exa: failed for %r — query: %r", competitor, query
            )

    articles.sort(key=lambda a: a.get("exa_score") or 0, reverse=True)
    logger.info("watch_news (exa): %d articles for %r", len(articles), competitor)
    return articles[:15]


# ---------------------------------------------------------------------------
# RSS fallback
# ---------------------------------------------------------------------------

async def _watch_news_rss(competitor: str) -> list[dict]:
    import httpx

    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser not installed; returning empty list")
        return []

    q = urllib.parse.quote(f'"{competitor}" company')
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "ScoutAgent/1.0"})
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
    except Exception:
        logger.exception("watch_news (rss): fetch failed for %r", competitor)
        return []

    articles: list[dict] = []
    for entry in feed.entries[:15]:
        articles.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published": _parse_rss_date(getattr(entry, "published", None)),
            "source": _rss_source(entry),
            "summary": entry.get("summary", "")[:500],
            "competitor": competitor,
            "exa_score": None,
        })

    logger.info("watch_news (rss): %d articles for %r", len(articles), competitor)
    return articles


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.removeprefix("www.")
    except Exception:
        return "web"


def _parse_rss_date(raw: str | None) -> str:
    if not raw:
        return datetime.now(timezone.utc).isoformat()
    try:
        import email.utils
        return email.utils.parsedate_to_datetime(raw).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _rss_source(entry) -> str:
    if hasattr(entry, "source") and hasattr(entry.source, "title"):
        return entry.source.title
    if hasattr(entry, "tags") and entry.tags:
        return entry.tags[0].get("term", "")
    return "news"
