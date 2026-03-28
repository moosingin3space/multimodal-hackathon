"""Scrape company websites — homepage, blog, press, and changelog pages."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_TIMEOUT = 12.0
_HEADERS = {"User-Agent": "ScoutAgent/1.0 (competitive intelligence bot)"}

# Company → primary domain (for known companies)
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


async def scrape_web(competitor: str) -> list[dict]:
    """Return scraped pages for *competitor* (blog, press, changelog)."""
    pages: list[dict] = []

    base_url = _resolve_base_url(competitor)
    urls_to_try = [base_url] if base_url else _guess_urls(competitor)

    async with httpx.AsyncClient(
        timeout=_TIMEOUT, headers=_HEADERS, follow_redirects=True
    ) as client:
        for url in urls_to_try[:3]:
            result = await _fetch_page(client, url, competitor)
            if result:
                pages.append(result)
                # Discover sub-pages from the page
                sub_urls = _extract_article_links(result.get("raw_html", ""), url)
                for sub_url in sub_urls[:5]:
                    sub_result = await _fetch_page(client, sub_url, competitor)
                    if sub_result:
                        pages.append(sub_result)

    logger.info("scrape_web: %d pages for %r", len(pages), competitor)
    return pages


def _resolve_base_url(competitor: str) -> str | None:
    return _KNOWN_DOMAINS.get(competitor.lower())


def _guess_urls(competitor: str) -> list[str]:
    slug = competitor.lower().replace(" ", "").replace(",", "").replace(".", "")
    base = f"https://www.{slug}.com"
    return [f"{base}{path}" for path in _BLOG_PATHS]


async def _fetch_page(
    client: httpx.AsyncClient, url: str, competitor: str
) -> dict | None:
    try:
        resp = await client.get(url)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else url

        # Extract meaningful text (remove nav, footer, scripts)
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)[:3000]
        return {
            "url": str(resp.url),
            "title": title_text[:200],
            "content": text,
            "raw_html": resp.text[:5000],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "competitor": competitor,
        }
    except Exception:
        logger.debug("_fetch_page: failed for %s", url)
        return None


def _extract_article_links(html: str, base_url: str) -> list[str]:
    """Extract article/post links from a page."""
    try:
        soup = BeautifulSoup(html, "lxml")
        base_domain = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
        links: list[str] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = urljoin(base_url, href)
            # Only follow same-domain links that look like articles
            if (
                full.startswith(base_domain)
                and any(kw in full for kw in ("/blog/", "/news/", "/press/", "/post/", "/article/"))
                and full != base_url
            ):
                links.append(full)
        return list(dict.fromkeys(links))[:8]  # deduplicate
    except Exception:
        return []
