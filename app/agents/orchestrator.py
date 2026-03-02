from __future__ import annotations

import asyncio
from collections.abc import Sequence

from app.agents.base import AgentResult, ReviewAgent
from app.github.models import ChangedFile, PullRequestContext


class AgentOrchestrator:
    def __init__(self, agents: Sequence[ReviewAgent]) -> None:
        self.agents = agents

    async def run_all(self, pr: PullRequestContext, files: Sequence[ChangedFile]) -> list[AgentResult]:
        tasks = [agent.run(pr, files) for agent in self.agents]
        results: list[AgentResult] = await asyncio.gather(*tasks)
        return results
