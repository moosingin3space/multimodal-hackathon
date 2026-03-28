"""Find competitor web content using Exa semantic search.

Replaces manual domain guessing + BeautifulSoup scraping with Exa's
neural search across company blogs, press releases, and changelogs.
Falls back to direct HTTP scraping when EXA_API_KEY is not set.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

_EXA_API_KEY = os.environ.get("EXA_API_KEY")
_TIMEOUT = 12.0
_HEADERS = {"User-Agent": "ScoutAgent/1.0 (competitive intelligence bot)"}


async def scrape_web(competitor: str) -> list[dict]:
    """Return recent web content for *competitor* (blog, press, changelog).

    Uses Exa when EXA_API_KEY is set; falls back to direct HTTP scraping.
    """
    if _EXA_API_KEY:
        return await _scrape_exa(competitor)
    return await _scrape_direct(competitor)


# ---------------------------------------------------------------------------
# Exa path
# ---------------------------------------------------------------------------

async def _scrape_exa(competitor: str) -> list[dict]:
    try:
        from exa_py import AsyncExa
    except ImportError:
        logger.warning("exa-py not installed — falling back to direct scraping")
        return await _scrape_direct(competitor)

    since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    queries = [
        f"{competitor} blog post announcement",
        f"{competitor} press release product update",
        f"site:{_slug(competitor)}.com",
    ]

    exa = AsyncExa(api_key=_EXA_API_KEY)
    seen_urls: set[str] = set()
    pages: list[dict] = []

    for query in queries:
        try:
            result = await exa.search(
                query,
                num_results=5,
                use_autoprompt=True,
                start_published_date=since,
                type="neural",
            )
            for item in result.results:
                url = item.url or ""
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                pages.append({
                    "url": url,
                    "title": item.title or "",
                    "content": (getattr(item, "text", None) or "")[:3000],
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "competitor": competitor,
                    "source": "exa",
                    "exa_score": getattr(item, "score", None),
                })
        except Exception:
            logger.exception(
                "_scrape_exa: failed for %r — query: %r", competitor, query
            )

    pages.sort(key=lambda p: p.get("exa_score") or 0, reverse=True)
    logger.info("scrape_web (exa): %d pages for %r", len(pages), competitor)
    return pages[:12]


# ---------------------------------------------------------------------------
# Direct HTTP fallback
# ---------------------------------------------------------------------------

_KNOWN_DOMAINS: dict[str, str] = {
    "cisco": "https://newsroom.cisco.com",
    "palo alto networks": "https://www.paloaltonetworks.com/blog",
    "fortinet": "https://www.fortinet.com/blog",
    "juniper networks": "https://blogs.juniper.net",
    "arista networks": "https://www.arista.com/en/company/news/press-releases",
    "check point software": "https://blog.checkpoint.com",
    "crowdstrike": "https://www.crowdstrike.com/blog",
    "zscaler": "https://www.zscaler.com/blogs",
    "sentinelone": "https://www.sentinelone.com/blog",
    "microsoft": "https://blogs.microsoft.com",
    "google": "https://blog.google",
    "openai": "https://openai.com/news",
    "anthropic": "https://www.anthropic.com/news",
}

_BLOG_PATHS = ["/blog", "/news", "/press", "/newsroom", "/changelog", "/announcements"]


async def _scrape_direct(competitor: str) -> list[dict]:
    import httpx
    from bs4 import BeautifulSoup

    base_url = _KNOWN_DOMAINS.get(competitor.lower())
    urls_to_try = [base_url] if base_url else _guess_urls(competitor)
    pages: list[dict] = []

    async with httpx.AsyncClient(
        timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True
    ) as client:
        for url in urls_to_try[:3]:
            result = await _fetch_page(client, url, competitor)
            if result:
                pages.append(result)
                for sub_url in _extract_article_links(result.get("raw_html", ""), url)[:5]:
                    sub = await _fetch_page(client, sub_url, competitor)
                    if sub:
                        pages.append(sub)

    logger.info("scrape_web (direct): %d pages for %r", len(pages), competitor)
    return pages


def _guess_urls(competitor: str) -> list[str]:
    base = f"https://www.{_slug(competitor)}.com"
    return [f"{base}{path}" for path in _BLOG_PATHS]


async def _fetch_page(client, url: str, competitor: str) -> dict | None:
    try:
        from bs4 import BeautifulSoup
        resp = await client.get(url)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        title = soup.find("title")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        return {
            "url": str(resp.url),
            "title": (title.get_text(strip=True) if title else url)[:200],
            "content": soup.get_text(separator=" ", strip=True)[:3000],
            "raw_html": resp.text[:5000],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "competitor": competitor,
            "source": "direct",
            "exa_score": None,
        }
    except Exception:
        logger.debug("_fetch_page: failed for %s", url)
        return None


def _extract_article_links(html: str, base_url: str) -> list[str]:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        base_domain = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
        links: list[str] = []
        for a in soup.find_all("a", href=True):
            full = urljoin(base_url, a["href"])
            if (
                full.startswith(base_domain)
                and any(kw in full for kw in ("/blog/", "/news/", "/press/", "/post/", "/article/"))
                and full != base_url
            ):
                links.append(full)
        return list(dict.fromkeys(links))[:8]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(competitor: str) -> str:
    return (
        competitor.lower()
        .replace(" ", "")
        .replace(",", "")
        .replace(".", "")
        .replace("-", "")
    )
