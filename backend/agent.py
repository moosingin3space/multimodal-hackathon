"""Railtracks orchestration loop — coordinates workers and signal extraction."""
from backend.signals.employee_signals import extract_employee_signals
from backend.signals.investor_signals import extract_investor_signals
from backend.signals.urgency_scorer import score_urgency
from backend.workers.github_watcher import watch_github
from backend.workers.image_analyzer import analyze_images
from backend.workers.jobs_watcher import watch_jobs
from backend.workers.news_watcher import watch_news
from backend.workers.web_scraper import scrape_web
from backend.memory import save_signals
from backend.synthesizer import synthesize


async def run_agent(company_name: str) -> None:
    """Run a full intelligence sweep for all competitors of *company_name*."""
    # TODO: load competitor list from memory / discovery
    competitors: list[str] = []

    for competitor in competitors:
        raw = await _gather(competitor)
        signals = (
            await extract_employee_signals(raw)
            + await extract_investor_signals(raw)
        )
        scored = [await score_urgency(s) for s in signals]
        await save_signals(competitor, scored)
        await synthesize(competitor, scored)


async def _gather(competitor: str) -> dict:
    web, news, jobs, github, images = await _run_all(
        scrape_web(competitor),
        watch_news(competitor),
        watch_jobs(competitor),
        watch_github(competitor),
        analyze_images(competitor),
    )
    return {
        "web": web,
        "news": news,
        "jobs": jobs,
        "github": github,
        "images": images,
    }


async def _run_all(*coros):
    import asyncio
    return await asyncio.gather(*coros)
