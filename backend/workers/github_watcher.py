"""Watch GitHub for repository activity, contributor growth, and new projects."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)

_GH_BASE = "https://api.github.com"
_TIMEOUT = 15.0

# Map company names → GitHub org slugs for known companies
_ORG_SLUGS: dict[str, str] = {
    "cisco": "cisco",
    "palo alto networks": "PaloAltoNetworks",
    "fortinet": "fortinet",
    "juniper networks": "Juniper",
    "arista networks": "aristanetworks",
    "check point software": "CheckPointSW",
    "crowdstrike": "CrowdStrike",
    "zscaler": "zscaler",
    "sentinelone": "Sentinel-One",
    "microsoft": "microsoft",
    "google": "google",
    "apple": "apple",
    "amazon": "aws",
    "meta": "facebookresearch",
    "openai": "openai",
    "anthropic": "anthropics",
    "stripe": "stripe",
    "salesforce": "salesforce",
}


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _org_slug(competitor: str) -> str:
    return _ORG_SLUGS.get(competitor.lower(), competitor.lower().replace(" ", ""))


async def watch_github(competitor: str) -> list[dict]:
    """Return GitHub activity signals for *competitor*."""
    org = _org_slug(competitor)
    signals: list[dict] = []

    try:
        async with httpx.AsyncClient(
            timeout=_TIMEOUT, headers=_headers(), follow_redirects=True
        ) as client:
            repos = await _get_repos(client, org)
            if not repos:
                return []

            for repo in repos[:10]:
                signal = await _analyze_repo(client, org, repo)
                if signal:
                    signals.append(signal)
    except Exception:
        logger.exception("watch_github: failed for %r (org=%r)", competitor, org)

    logger.info("watch_github: %d signals for %r", len(signals), competitor)
    return signals


async def _get_repos(client: httpx.AsyncClient, org: str) -> list[dict]:
    resp = await client.get(
        f"{_GH_BASE}/orgs/{org}/repos",
        params={"sort": "updated", "per_page": 15, "type": "public"},
    )
    if resp.status_code == 404:
        # Try user endpoint as fallback
        resp = await client.get(
            f"{_GH_BASE}/users/{org}/repos",
            params={"sort": "updated", "per_page": 15, "type": "public"},
        )
    if resp.status_code != 200:
        return []
    return resp.json()


async def _analyze_repo(
    client: httpx.AsyncClient, org: str, repo: dict
) -> dict | None:
    name = repo.get("name", "")
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    description = repo.get("description", "") or ""
    url = repo.get("html_url", "")
    pushed = repo.get("pushed_at", "")
    created = repo.get("created_at", "")

    # Only surface recently active repos
    if not pushed:
        return None
    try:
        pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - pushed_dt).days
        if age_days > 30:
            return None
    except Exception:
        pass

    # Get commit count for last 30 days
    commits_30d = await _commits_last_30d(client, org, name)

    # Get contributor count
    contributors = await _contributor_count(client, org, name)

    return {
        "repo": name,
        "full_name": f"{org}/{name}",
        "stars": stars,
        "forks": forks,
        "commits_30d": commits_30d,
        "contributors": contributors,
        "description": description[:200],
        "url": url,
        "pushed_at": pushed,
        "created_at": created,
        "is_new": _is_new(created),
    }


async def _commits_last_30d(
    client: httpx.AsyncClient, org: str, repo: str
) -> int:
    since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    resp = await client.get(
        f"{_GH_BASE}/repos/{org}/{repo}/commits",
        params={"since": since, "per_page": 100},
    )
    if resp.status_code != 200:
        return 0
    return len(resp.json())


async def _contributor_count(
    client: httpx.AsyncClient, org: str, repo: str
) -> int:
    resp = await client.get(
        f"{_GH_BASE}/repos/{org}/{repo}/contributors",
        params={"per_page": 1, "anon": "false"},
    )
    if resp.status_code != 200:
        return 0
    # GitHub returns total count in Link header; approximate from page
    link = resp.headers.get("Link", "")
    if 'rel="last"' in link:
        import re
        m = re.search(r'page=(\d+)>; rel="last"', link)
        if m:
            return int(m.group(1))
    return len(resp.json())


def _is_new(created_at: str) -> bool:
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days <= 30
    except Exception:
        return False
