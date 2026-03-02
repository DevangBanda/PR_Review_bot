# ruff: noqa: I001
from __future__ import annotations

from fastapi import FastAPI

from app.config import settings
from app.logging import setup_logging
from app.webhooks.github import router as github_router


setup_logging(settings.log_level)

app = FastAPI(
    title="PR Agent Review Bot",
    version="0.1.0",
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(github_router)
