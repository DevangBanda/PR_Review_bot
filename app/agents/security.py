from __future__ import annotations

import re
from collections.abc import Sequence

from app.agents.base import AgentFinding, AgentResult
from app.github.models import ChangedFile, PullRequestContext

SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "Possible AWS access key"),
    (re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"), "Possible API key assignment"),
    (re.compile(r"(?i)secret\s*[:=]\s*['\"][^'\"]{8,}['\"]"), "Possible secret assignment"),
    (re.compile(r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----"), "Private key material detected"),
]

RISKY_COMMANDS = [
    "curl | sh",
    "wget | sh",
    "chmod 777",
]


class SecurityAgent:
    name = "Security"

    async def run(
        self,
        pr: PullRequestContext,
        files: Sequence[ChangedFile],
    ) -> AgentResult:

        findings: list[AgentFinding] = []

        for f in files:
            patch = f.patch or ""
            if not patch:
                continue

            patch_lines = patch.split("\n")

            for i, line in enumerate(patch_lines):

                # Only consider added lines in diff
                if not line.startswith("+") or line.startswith("+++"):
                    continue

                # Check for secret patterns
                for pattern, msg in SECRET_PATTERNS:
                    if pattern.search(line):
                        findings.append(
                            AgentFinding(
                                title=msg,
                                severity="high",
                                details=f"Hardcoded secret detected in `{f.filename}`.",
                                file_path=f.filename,
                                line_number=i + 1,  # diff position
                            )
                        )

                # Check for risky shell commands
                lowered_line = line.lower()
                for cmd in RISKY_COMMANDS:
                    if cmd in lowered_line:
                        findings.append(
                            AgentFinding(
                                title="Risky shell pattern",
                                severity="medium",
                                details=f"Found `{cmd}` usage in `{f.filename}`.",
                                file_path=f.filename,
                                line_number=i + 1,
                            )
                        )

        summary = (
            "No obvious secrets or high-risk patterns detected."
            if not findings
            else "Potential security issues found."
        )

        return AgentResult(
            agent_name=self.name,
            summary=summary,
            findings=findings,
        )