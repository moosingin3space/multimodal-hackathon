"""Streaming chat endpoint for the assistant-ui frontend."""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.auth import require_api_key
from backend.synthesizer import stream_chat

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/chat")
async def chat(prompt: str) -> StreamingResponse:
    return StreamingResponse(stream_chat(prompt), media_type="text/event-stream")
