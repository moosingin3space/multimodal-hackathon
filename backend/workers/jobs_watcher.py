"""Watch job postings to detect hiring signals — LinkedIn/Indeed/Greenhouse via RSS & scraping."""
from __future__ import annotations

import logging
import urllib.parse
from datetime import datetime, timezone

import feedparser
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_TIMEOUT = 10.0


async def watch_jobs(competitor: str) -> list[dict]:
    """Return open job postings for *competitor*.

    Tries multiple sources in order, merging results.
    """
    results: list[dict] = []

    # 1. Google News search for "{competitor} hiring" signals
    results.extend(await _google_jobs_news(competitor))

    # 2. Try Greenhouse (many tech companies use this ATS publicly)
    results.extend(await _greenhouse_jobs(competitor))

    logger.info("watch_jobs: %d postings for %r", len(results), competitor)
    return results


async def _google_jobs_news(competitor: str) -> list[dict]:
    q = urllib.parse.quote(f'"{competitor}" hiring jobs')
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "ScoutAgent/1.0"})
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
    except Exception:
        logger.debug("_google_jobs_news: failed for %r", competitor)
        return []

    jobs: list[dict] = []
    for entry in feed.entries[:10]:
        title = entry.get("title", "")
        if any(kw in title.lower() for kw in ("hiring", "job", "career", "recruit", "talent")):
            jobs.append(
                {
                    "title": title,
                    "url": entry.get("link", ""),
                    "company": competitor,
                    "date": datetime.now(timezone.utc).isoformat(),
                    "source": "google_news",
                    "description": entry.get("summary", "")[:400],
                }
            )
    return jobs


async def _greenhouse_jobs(competitor: str) -> list[dict]:
    """Try the public Greenhouse job board for *competitor* (slug = lowercase-no-spaces)."""
    slug = competitor.lower().replace(" ", "").replace(".", "").replace(",", "")
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            data = resp.json()
    except Exception:
        return []

    jobs: list[dict] = []
    for job in data.get("jobs", [])[:20]:
        jobs.append(
            {
                "title": job.get("title", ""),
                "url": job.get("absolute_url", ""),
                "company": competitor,
                "date": datetime.now(timezone.utc).isoformat(),
                "source": "greenhouse",
                "location": ", ".join(
                    o.get("name", "") for o in job.get("offices", [])
                ),
                "department": ", ".join(
                    d.get("name", "") for d in job.get("departments", [])
                ),
                "description": _strip_html(job.get("content", ""))[:400],
            }
        )
    return jobs


def _strip_html(html: str) -> str:
    try:
        return BeautifulSoup(html, "lxml").get_text(separator=" ").strip()
    except Exception:
        return html
