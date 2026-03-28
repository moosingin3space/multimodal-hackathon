"""YouTube search tool via yt-dlp for use by LangGraph agents."""
import asyncio
import json

from langchain_core.tools import tool


@tool
async def yt_search(query: str, max_results: int = 10) -> str:
    """Search YouTube for videos using yt-dlp.

    Args:
        query: The search query. Be specific — include the company name plus the
               type of content (e.g. "Stripe CEO interview 2025").
        max_results: Number of results to fetch. Default 10.

    Returns:
        JSON string — a list of {title, url, channel, views, upload_date,
        duration_s, description}.
    """
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-warnings",
        "--flat-playlist",
        f"ytsearch{max_results}:{query}",
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await proc.communicate()

    videos = []
    for line in stdout.decode(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        video_id = data.get("id", "")
        url = data.get("webpage_url") or (
            f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
        )
        if not url:
            continue

        raw_date = data.get("upload_date", "")
        if len(raw_date) == 8 and raw_date.isdigit():
            upload_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
        else:
            upload_date = raw_date

        videos.append(
            {
                "title": data.get("title", ""),
                "url": url,
                "channel": data.get("uploader") or data.get("channel", ""),
                "views": data.get("view_count") or 0,
                "upload_date": upload_date,
                "duration_s": data.get("duration") or 0,
                "description": (data.get("description") or "")[:300],
            }
        )

    return json.dumps(videos)
