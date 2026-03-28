"""FastAPI application with Unkey auth middleware."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import agent, chat, discover

app = FastAPI(title="ScoutAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: add Unkey middleware
# from unkey import UnkeyMiddleware
# app.add_middleware(UnkeyMiddleware, api_id=os.environ["UNKEY_API_ID"])

app.include_router(discover.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
