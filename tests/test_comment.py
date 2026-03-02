from __future__ import annotations

from app.agents.base import AgentFinding, AgentResult
from app.services.reviewer import attach_fingerprint, build_comment


def test_build_comment_contains_marker():
    results = [
        AgentResult(agent_name="Security", summary="ok", findings=[AgentFinding("t", "low", "d")]),
    ]
    body = build_comment("http://x", "abc123def456", results)
    assert "PR Agent Review" in body
    assert "Security" in body


def test_attach_fingerprint():
    body = attach_fingerprint("hello", "abc")
    assert "fingerprint:" in body
