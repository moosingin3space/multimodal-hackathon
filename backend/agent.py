"""Railtracks orchestration loop — coordinates parallel workers and signal extraction."""
from __future__ import annotations

import asyncio
import logging

from backend.discovery import discover_competitors
from backend.memory import load_competitors, save_competitors, save_signals
from backend.signals.employee_signals import extract_employee_signals
from backend.signals.investor_signals import extract_investor_signals
from backend.signals.urgency_scorer import score_urgency
from backend.workers.github_watcher import watch_github
from backend.workers.image_analyzer import analyze_images
from backend.workers.jobs_watcher import watch_jobs
from backend.workers.news_watcher import watch_news
from backend.workers.web_scraper import scrape_web

logger = logging.getLogger(__name__)


async def run_agent(company_name: str) -> dict:
    """Run a full intelligence sweep for all competitors of *company_name*.

    1. Load (or discover) competitor list
    2. For each competitor, run all workers in parallel
    3. Extract + score signals
    4. Deduplicate via memory and save new signals
    5. Return summary of what was found
    """
    # Step 1: ensure we have a competitor list
    competitors = await load_competitors(company_name)
    if not competitors:
        logger.info("run_agent: discovering competitors for %r", company_name)
        competitors = await discover_competitors(company_name)
        await save_competitors(company_name, competitors)

    logger.info(
        "run_agent: sweeping %d competitors for %r", len(competitors), company_name
    )

    results: dict[str, list[dict]] = {}
    sweep_tasks = [_sweep_competitor(c) for c in competitors]
    competitor_results = await asyncio.gather(*sweep_tasks, return_exceptions=True)

    total_new = 0
    for competitor, result in zip(competitors, competitor_results):
        if isinstance(result, Exception):
            logger.error("run_agent: sweep failed for %r: %s", competitor, result)
            results[competitor] = []
            continue

        new_signals = await save_signals(competitor, result)
        results[competitor] = new_signals
        total_new += len(new_signals)
        logger.info(
            "run_agent: %d new signals for %r", len(new_signals), competitor
        )

    logger.info("run_agent: sweep complete — %d total new signals", total_new)
    return {
        "company": company_name,
        "competitors_swept": len(competitors),
        "new_signals": total_new,
        "breakdown": {c: len(s) for c, s in results.items()},
    }


async def _sweep_competitor(competitor: str) -> list[dict]:
    """Run all workers in parallel for *competitor*, then extract and score signals."""
    # Run all workers in parallel
    web_task = asyncio.create_task(scrape_web(competitor))
    news_task = asyncio.create_task(watch_news(competitor))
    jobs_task = asyncio.create_task(watch_jobs(competitor))
    github_task = asyncio.create_task(watch_github(competitor))

    web, news, jobs, github = await asyncio.gather(
        web_task, news_task, jobs_task, github_task, return_exceptions=True
    )

    def _safe(result, default):
        return result if not isinstance(result, Exception) else default

    # Collect image URLs for Gemini analysis
    image_urls: list[str] = []
    for article in (_safe(news, []) or [])[:5]:
        if article.get("image_url"):
            image_urls.append(article["image_url"])

    images = await analyze_images(competitor, image_urls)

    raw = {
        "competitor": competitor,
        "web": _safe(web, []),
        "news": _safe(news, []),
        "jobs": _safe(jobs, []),
        "github": _safe(github, []),
        "images": images,
    }

    # Extract signals from both modes in parallel
    employee_task = asyncio.create_task(extract_employee_signals(raw))
    investor_task = asyncio.create_task(extract_investor_signals(raw))
    employee_signals, investor_signals = await asyncio.gather(
        employee_task, investor_task, return_exceptions=True
    )

    all_signals = [
        *(_safe(employee_signals, [])),
        *(_safe(investor_signals, [])),
    ]

    # Attach Gemini analysis to relevant signals
    if images:
        for signal in all_signals:
            if not signal.get("gemini_analysis") and images:
                signal["gemini_analysis"] = images[0].get("key_finding")
                signal["image_url"] = signal.get("image_url") or images[0].get("image_url")

    # Score urgency for all signals
    scored = await asyncio.gather(*(score_urgency(s) for s in all_signals))
    return list(scored)
