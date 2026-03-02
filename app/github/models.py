from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int


@dataclass(frozen=True)
class PullRequestContext:
    pr: PullRequestRef
    title: str
    body: str
    html_url: str
    changed_files: int
    additions: int
    deletions: int
    head_sha: str


@dataclass(frozen=True)
class ChangedFile:
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str | None  # may be absent for binary or large files
