"""DigitalOcean inference — build trajectory summaries and stream chat."""
import os
from typing import AsyncGenerator

from gradient import AsyncGradient


async def synthesize(competitor: str, signals: list[dict]) -> str:
    """Summarise *signals* into a trajectory narrative for *competitor*."""
    # TODO: build prompt from signals and call inference
    raise NotImplementedError


async def stream_chat(prompt: str) -> AsyncGenerator[str, None]:
    """Stream a chat response from Gradient inference."""
    client = AsyncGradient(
        inference_endpoint="https://inference.do-ai.run",
        model_access_key=os.environ["GRADIENT_MODEL_ACCESS_KEY"],
    )
    stream = await client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai-gpt-oss-120b",
        stream=True,
    )
    async for event in stream:
        delta = event.choices[0].delta.content
        if delta:
            yield f"data: {delta}\n\n"
