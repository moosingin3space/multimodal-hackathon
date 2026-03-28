"""Exa web-search tool for use by LangGraph agents."""
import json
import os
from datetime import datetime, timedelta, timezone

from exa_py import Exa
from langchain_core.tools import tool


@tool
def exa_search(query: str, days_back: int = 90) -> str:
    """Search the web for recent articles and pages using Exa neural search.

    Args:
        query: The search query. Be specific — include the company name plus the
               topic you want (e.g. "Stripe product launch 2025").
        days_back: How many days back to search. Default 90.

    Returns:
        JSON string — a list of {title, url, published_date, highlights, summary}.
    """
    exa = Exa(api_key=os.environ["EXA_API_KEY"])
    start_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    response = exa.search_and_contents(
        query,
        num_results=10,
        type="neural",
        start_published_date=start_date,
        highlights={"num_sentences": 3, "highlights_per_url": 2},
        summary={"query": query},
    )
    results = [
        {
            "title": r.title or "",
            "url": r.url,
            "published_date": r.published_date or "",
            "highlights": r.highlights or [],
            "summary": r.summary or "",
        }
        for r in response.results
    ]
    return json.dumps(results)
