"""Local test harness — runs all three agents for a given company name.

Usage:
    uv run python run_agents.py "Stripe"
    uv run python run_agents.py "Stripe" --agent news
    uv run python run_agents.py "Stripe" --agent competitors
    uv run python run_agents.py "Stripe" --agent youtube
"""
import argparse
import asyncio
import json
import sys

from dotenv import load_dotenv

load_dotenv()


async def run_news(company: str) -> None:
    from agents.news_agent import run
    print(f"\n{'='*60}")
    print(f"NEWS AGENT  →  {company}")
    print("="*60)
    results = await run(company)
    for i, a in enumerate(results, 1):
        score = a.get("relevancy_score", "?")
        print(f"\n[{i}] ({score}/10) {a.get('title', '')}")
        print(f"    {a.get('url', '')}")
        print(f"    {a.get('published_date', '')}  —  {a.get('summary', '')}")


async def run_competitors(company: str) -> None:
    from agents.competitor_agent import run
    print(f"\n{'='*60}")
    print(f"COMPETITOR AGENT  →  {company}")
    print("="*60)
    results = await run(company)
    for i, name in enumerate(results, 1):
        print(f"  {i:>2}. {name}")


async def run_youtube(company: str) -> None:
    from agents.youtube_agent import run
    print(f"\n{'='*60}")
    print(f"YOUTUBE AGENT  →  {company}")
    print("="*60)
    results = await run(company)
    for i, v in enumerate(results, 1):
        score = v.get("relevancy_score", "?")
        print(f"\n[{i}] ({score}/10) {v.get('title', '')}")
        print(f"    {v.get('url', '')}")
        print(f"    {v.get('channel', '')}  •  {v.get('views', 0):,} views  •  {v.get('upload_date', '')}")
        print(f"    {v.get('reason', '')}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run scout agents locally")
    parser.add_argument("company", help="Company name to research")
    parser.add_argument(
        "--agent",
        choices=["news", "competitors", "youtube", "all"],
        default="all",
        help="Which agent to run (default: all)",
    )
    args = parser.parse_args()

    runners = {
        "news": run_news,
        "competitors": run_competitors,
        "youtube": run_youtube,
    }

    if args.agent == "all":
        for fn in runners.values():
            await fn(args.company)
    else:
        await runners[args.agent](args.company)


if __name__ == "__main__":
    asyncio.run(main())
