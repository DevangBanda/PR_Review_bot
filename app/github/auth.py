from __future__ import annotations

import time

import httpx
import jwt
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.logging import get_logger

log = get_logger(__name__)


def _build_app_jwt(app_id: int, private_key_pem: str) -> str:
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 9 * 60,  # GitHub requires <10 minutes
        "iss": str(app_id),
    }
    token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    # PyJWT types can be Any; normalize to str
    return token if isinstance(token, str) else token.decode("utf-8")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
async def get_installation_token(
    http: httpx.AsyncClient,
    installation_id: int,
    app_id: int,
    private_key_pem: str,
) -> str:
    app_jwt = _build_app_jwt(app_id, private_key_pem)
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
    }
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    resp = await http.post(url, headers=headers, json={})
    resp.raise_for_status()
    data = resp.json()
    token = data.get("token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("GitHub installation token missing from response.")
    return token


def resolve_github_auth_mode() -> str:
    if settings.github_token:
        return "pat"
    if settings.github_app_id and settings.github_installation_id and settings.github_private_key():
        return "app"
    return "none"
