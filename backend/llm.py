"""Shared Gradient / DigitalOcean inference client factory."""
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

GRADIENT_ENDPOINT = "https://inference.do-ai.run/v1"
DEFAULT_MODEL = "openai-gpt-oss-120b"


def make_llm(model: str = DEFAULT_MODEL, **kwargs) -> ChatOpenAI:
    """Return a ChatOpenAI client pointed at DigitalOcean Serverless Inference."""
    return ChatOpenAI(
        model=model,
        openai_api_base=GRADIENT_ENDPOINT,
        openai_api_key=os.environ["GRADIENT_MODEL_ACCESS_KEY"],
        **kwargs,
    )
