from __future__ import annotations

import hashlib
import hmac
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from app.agents.orchestrator import AgentOrchestrator
from app.agents.performance import PerformanceAgent
from app.agents.security import SecurityAgent
from app.agents.style import StyleAgent
from app.comments.formatter import severity_icon
from app.config import settings
from app.github.client import GitHubClient
from app.github.models import PullRequestRef
from app.logging import get_logger
from app.services.reviewer import (
    already_commented_for_sha,
    attach_fingerprint,
    build_comment,
)

log = get_logger(__name__)

router = APIRouter()


def verify_signature(body: bytes, signature_256: str | None) -> None:
    secret = settings.github_webhook_secret.encode("utf-8")
    if not secret or settings.github_webhook_secret == "change_me":
        raise HTTPException(status_code=500, detail="Webhook secret is not configured (GITHUB_WEBHOOK_SECRET).")

    if not signature_256 or not signature_256.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing or invalid X-Hub-Signature-256 header.")

    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    provided = signature_256.split("=", 1)[1]

    if not hmac.compare_digest(expected, provided):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")


def should_process_event(event: str, payload: dict) -> bool:
    if event != "pull_request":
        return False
    action = payload.get("action")
    return action in {"opened", "reopened", "synchronize", "ready_for_review"}


@router.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, Any]:
    body = await request.body()
    verify_signature(body, x_hub_signature_256)
    payload = await request.json()

    if not should_process_event(x_github_event, payload):
        return {"ok": True, "ignored": True}

    pr_data = payload.get("pull_request") or {}
    repo = payload.get("repository") or {}
    owner = ((repo.get("owner") or {}).get("login")) or ""
    repo_name = repo.get("name") or ""
    pr_number = int(pr_data.get("number") or 0)

    if not owner or not repo_name or pr_number <= 0:
        raise HTTPException(status_code=400, detail="Invalid pull_request payload (missing owner/repo/number).")

    pr = PullRequestRef(owner=owner, repo=repo_name, number=pr_number)

    gh = GitHubClient()
    try:
        ctx = await gh.fetch_pr_context(pr)
        files = await gh.list_changed_files(pr)

        if await already_commented_for_sha(gh, pr, ctx.head_sha):
            return {"ok": True, "skipped": "already_commented_for_sha"}

        orchestrator = AgentOrchestrator([SecurityAgent(), PerformanceAgent(), StyleAgent()])
        results = await orchestrator.run_all(ctx, files)

        # NEW: Post inline file-level comments
        for r in results:
            for f in r.findings:
                if hasattr(f, "file_path") and hasattr(f, "line_number"):
                    try:
                        await gh.post_inline_review_comment(
                            pr=pr,
                            body=f"{severity_icon(f.severity)} — {f.details}",
                            path=f.file_path,
                            line=f.line_number,
                            commit_id=ctx.head_sha,
                        )
                    except Exception as e:
                        log.warning(f"Inline comment failed: {e}")

        # Then post the summary report
        comment = build_comment(ctx.html_url, ctx.head_sha, results)
        comment = attach_fingerprint(comment, ctx.head_sha)

        await gh.post_pr_comment(pr, comment)
        return {"ok": True, "commented": True}
    finally:
        await gh.aclose()
