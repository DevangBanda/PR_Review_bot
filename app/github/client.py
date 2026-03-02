from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.github.auth import get_installation_token, resolve_github_auth_mode
from app.github.models import ChangedFile, PullRequestContext, PullRequestRef
from app.logging import get_logger

log = get_logger(__name__)


class GitHubClient:
    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=20.0)
        self._token: str | None = None

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _ensure_token(self) -> str:
        mode = resolve_github_auth_mode()
        if mode == "pat":
            assert settings.github_token
            return settings.github_token
        if mode == "app":
            if self._token:
                return self._token
            assert settings.github_app_id and settings.github_installation_id
            private_key = settings.github_private_key()
            assert private_key
            token = await get_installation_token(
                self._http,
                installation_id=settings.github_installation_id,
                app_id=settings.github_app_id,
                private_key_pem=private_key,
            )
            self._token = token
            return token
        raise RuntimeError("GitHub auth not configured. Set GITHUB_TOKEN or GitHub App credentials.")

    async def _headers(self) -> dict:
        token = await self._ensure_token()
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "pr-agent-review-bot",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def fetch_pr_context(self, pr: PullRequestRef) -> PullRequestContext:
        url = f"https://api.github.com/repos/{pr.owner}/{pr.repo}/pulls/{pr.number}"
        resp = await self._http.get(url, headers=await self._headers())
        resp.raise_for_status()
        data = resp.json()
        return PullRequestContext(
            pr=pr,
            title=data.get("title") or "",
            body=data.get("body") or "",
            html_url=data.get("html_url") or "",
            changed_files=int(data.get("changed_files") or 0),
            additions=int(data.get("additions") or 0),
            deletions=int(data.get("deletions") or 0),
            head_sha=(data.get("head") or {}).get("sha") or "",
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def list_changed_files(self, pr: PullRequestRef, per_page: int = 100) -> list[ChangedFile]:
        files: list[ChangedFile] = []
        page = 1
        while True:
            url = f"https://api.github.com/repos/{pr.owner}/{pr.repo}/pulls/{pr.number}/files"
            resp = await self._http.get(url, headers=await self._headers(), params={"per_page": per_page, "page": page})
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            for f in batch:
                files.append(
                    ChangedFile(
                        filename=f.get("filename") or "",
                        status=f.get("status") or "",
                        additions=int(f.get("additions") or 0),
                        deletions=int(f.get("deletions") or 0),
                        changes=int(f.get("changes") or 0),
                        patch=f.get("patch"),
                    )
                )
            if len(batch) < per_page:
                break
            page += 1
        return files

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def post_pr_comment(self, pr: PullRequestRef, body: str) -> None:
        url = f"https://api.github.com/repos/{pr.owner}/{pr.repo}/issues/{pr.number}/comments"
        resp = await self._http.post(url, headers=await self._headers(), json={"body": body})
        resp.raise_for_status()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def post_inline_review_comment(
        self,
        pr: PullRequestRef,
        body: str,
        path: str,
        line: int,
        commit_id: str,
    ) -> None:
        url = f"https://api.github.com/repos/{pr.owner}/{pr.repo}/pulls/{pr.number}/comments"

        payload = {
            "body": body,
            "commit_id": commit_id,
            "path": path,
            "line": line,
            "side": "RIGHT"
        }

        resp = await self._http.post(url, headers=await self._headers(), json=payload)
        resp.raise_for_status()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def list_issue_comments(self, pr: PullRequestRef, per_page: int = 100) -> list[dict[str, object]]:
        url = f"https://api.github.com/repos/{pr.owner}/{pr.repo}/issues/{pr.number}/comments"
        resp = await self._http.get(url, headers=await self._headers(), params={"per_page": per_page})
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            raise RuntimeError('Unexpected GitHub response type for comments')
        return data  # type: ignore[return-value]
