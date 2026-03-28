"""Streaming chat endpoint — grounded in current competitive signals."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.auth import require_api_key
from backend.memory import load_all_signals
from backend.synthesizer import stream_chat

router = APIRouter(dependencies=[Depends(require_api_key)])


class ChatRequest(BaseModel):
    prompt: str
    company: str | None = None


@router.post("/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    """Stream a chat response grounded in signals for *req.company*."""
    context_signals: list[dict] = []
    if req.company:
        context_signals = await load_all_signals(req.company, limit=30)

    return StreamingResponse(
        stream_chat(req.prompt, context_signals),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
