from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, Optional

from app.github.models import ChangedFile, PullRequestContext


@dataclass(frozen=True)
class AgentFinding:
    title: str
    severity: str
    details: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None


@dataclass(frozen=True)
class AgentResult:
    agent_name: str
    summary: str
    findings: Sequence[AgentFinding]


class ReviewAgent(Protocol):
    name: str

    async def run(
        self,
        pr: PullRequestContext,
        files: Sequence[ChangedFile],
    ) -> AgentResult: ...