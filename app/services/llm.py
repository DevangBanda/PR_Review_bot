from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import settings


@dataclass(frozen=True)
class LLMResponse:
    text: str


class LLMClient:
    async def complete(self, prompt: str) -> LLMResponse | None:
        if settings.llm_provider == "none":
            return None
        if settings.llm_provider != "openai_compatible":
            return None
        if not settings.llm_api_key:
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{settings.llm_api_base.rstrip('/')}/chat/completions"
            payload = {
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": "You are a senior software engineer reviewing a pull request."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return LLMResponse(text=text)
