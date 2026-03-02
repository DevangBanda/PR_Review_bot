from __future__ import annotations

import re
from collections.abc import Sequence

from app.agents.base import AgentFinding, AgentResult
from app.github.models import ChangedFile, PullRequestContext


class StyleAgent:
    name = "Style"

    async def run(self, pr: PullRequestContext, files: Sequence[ChangedFile]) -> AgentResult:
        findings: list[AgentFinding] = []

        for f in files:
            patch = f.patch or ""
            if not patch:
                continue

            if re.search(r"\+\s*print\(", patch):
                findings.append(
                    AgentFinding(
                        title="Debug prints added",
                        severity="low",
                        details=f"`{f.filename}`: `print()` added. Prefer structured logger or remove before merge.",
                    )
                )

            if re.search(r"\+\s*TODO\b", patch):
                findings.append(
                    AgentFinding(
                        title="TODO added",
                        severity="low",
                        details=f"`{f.filename}`: TODO comment added. Ensure it is tracked with an issue/task.",
                    )
                )

            if re.search(r"\+\s*var\s+\w+\s*=", patch) and f.filename.endswith((".js", ".ts", ".tsx")):
                findings.append(
                    AgentFinding(
                        title="Use let/const instead of var",
                        severity="low",
                        details=f"`{f.filename}`: `var` added. Prefer `const`/`let`.",
                    )
                )

        summary = "No major style issues detected." if not findings else "Minor style issues found."
        return AgentResult(agent_name=self.name, summary=summary, findings=findings)
