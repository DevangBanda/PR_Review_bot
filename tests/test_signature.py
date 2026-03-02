from __future__ import annotations

import hashlib
import hmac

import pytest
from fastapi import HTTPException

from app.config import settings
from app.webhooks.github import verify_signature


def test_verify_signature_valid(monkeypatch):
    monkeypatch.setattr(settings, "github_webhook_secret", "testsecret", raising=False)
    body = b'{"hello":"world"}'
    sig = hmac.new(b"testsecret", body, hashlib.sha256).hexdigest()
    verify_signature(body, f"sha256={sig}")


def test_verify_signature_invalid(monkeypatch):
    monkeypatch.setattr(settings, "github_webhook_secret", "testsecret", raising=False)
    body = b'{"hello":"world"}'
    with pytest.raises(HTTPException):
        verify_signature(body, "sha256=deadbeef")
