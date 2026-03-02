from __future__ import annotations

import re
from collections.abc import Sequence

from app.agents.base import AgentFinding, AgentResult
from app.github.models import ChangedFile, PullRequestContext


class PerformanceAgent:
    name = "Performance"

    async def run(self, pr: PullRequestContext, files: Sequence[ChangedFile]) -> AgentResult:
        findings: list[AgentFinding] = []

        for f in files:
            patch = f.patch or ""
            if not patch:
                continue

            # Heuristics (language-agnostic-ish)
            if re.search(r"for\s+\w+\s+in\s+\w+\s*:\s*\n\+\s*.*(select|query|find|fetch)", patch, re.I):
                findings.append(
                    AgentFinding(
                        title="Possible N+1 query pattern",
                        severity="medium",
                        details=f"`{f.filename}`: loop contains DB/IO call hints. Consider batching or prefetching.",
                    )
                )

            if re.search(r"\+\s*await\s+.*\n\+\s*for\s+.*\n", patch):
                findings.append(
                    AgentFinding(
                        title="Await inside loop",
                        severity="low",
                        details=f"`{f.filename}`: `await` in a loop can be slow. Consider `gather` / concurrency when safe.",
                    )
                )

            if re.search(r"\+\s*sleep\(", patch):
                findings.append(
                    AgentFinding(
                        title="Sleep added",
                        severity="low",
                        details=f"`{f.filename}`: added sleep. Ensure it is necessary and not on request path.",
                    )
                )

        summary = "No obvious performance smells detected." if not findings else "Potential performance improvements identified."
        return AgentResult(agent_name=self.name, summary=summary, findings=findings)
