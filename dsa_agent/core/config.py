"""DSA Agent global configuration."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    TUSHARE_TOKEN: str = "1f2efbb5be1015f9ee92da4513e9fe5eea847f9722b9a06cbaf80b26"
    BOCHA_API_KEY: str = "sk-551e1ff0c5ae48a3b5d6dd0f8be950810"
    OPENROUTER_API_KEY: str = "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"

    DSA_PRIMARY_MODEL: str = "xiaomi/mimo-v2.5"
    DSA_FALLBACK_MODEL: str = "deepseek/deepseek-v4-flash"

    LEGACY_API_URL: str = "http://1.94.7.13:5186"
    DSA_PORT: int = 8120
    DSA_HOST: str = "0.0.0.0"

    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    REQUEST_TIMEOUT: int = 30

    @property
    def is_configured(self) -> bool:
        return bool(self.OPENROUTER_API_KEY and self.TUSHARE_TOKEN)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()