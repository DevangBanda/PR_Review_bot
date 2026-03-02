from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["dev", "prod"] = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8080, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    github_webhook_secret: str = Field(default="", alias="GITHUB_WEBHOOK_SECRET")

    # GitHub App auth
    github_app_id: int | None = Field(default=None, alias="GITHUB_APP_ID")
    github_installation_id: int | None = Field(default=None, alias="GITHUB_INSTALLATION_ID")
    github_private_key_pem: str | None = Field(default=None, alias="GITHUB_PRIVATE_KEY_PEM")
    github_private_key_path: Path | None = Field(default=None, alias="GITHUB_PRIVATE_KEY_PATH")

    # PAT fallback
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")

    # LLM (optional)
    llm_provider: Literal["none", "openai_compatible"] = Field(default="none", alias="LLM_PROVIDER")
    llm_api_base: str = Field(default="https://api.openai.com/v1", alias="LLM_API_BASE")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")

    def github_private_key(self) -> str | None:
        if self.github_private_key_pem:
            # allow literal \n sequences in env var
            return self.github_private_key_pem.replace("\\n", "\n")
        if self.github_private_key_path and self.github_private_key_path.exists():
            return self.github_private_key_path.read_text(encoding="utf-8")
        return None


settings = Settings()
