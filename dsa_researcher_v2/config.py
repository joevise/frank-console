# -*- coding: utf-8 -*-
"""配置管理 — Tushare token + OpenRouter LLM 配置。"""

from __future__ import annotations

import os
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_TUSHARE_TOKEN: str = os.environ.get("TUSHARE_TOKEN", "")
DEFAULT_OPENROUTER_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")
DEFAULT_PRIMARY_MODEL: str = "xiaomi/mimo-v2.5"
DEFAULT_FALLBACK_MODEL: str = "deepseek/deepseek-v4-flash"
DEFAULT_REQUEST_TIMEOUT: int = 30
DEFAULT_CACHE_TTL: int = 300  # 5 分钟


class ResearcherConfig:
    """轻量配置容器。"""

    def __init__(
        self,
        tushare_token: Optional[str] = None,
        openrouter_key: Optional[str] = None,
        primary_model: str = DEFAULT_PRIMARY_MODEL,
        fallback_model: str = DEFAULT_FALLBACK_MODEL,
        request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
        cache_ttl: int = DEFAULT_CACHE_TTL,
    ):
        self.tushare_token = tushare_token or DEFAULT_TUSHARE_TOKEN
        self.openrouter_key = openrouter_key or DEFAULT_OPENROUTER_KEY
        self.primary_model = primary_model
        self.fallback_model = fallback_model

        # 写入环境变量，让 data_provider 内部能读到
        if self.tushare_token:
            os.environ["TUSHARE_TOKEN"] = self.tushare_token
        if self.openrouter_key:
            os.environ["OPENROUTER_API_KEY"] = self.openrouter_key


@lru_cache(maxsize=1)
def get_config() -> ResearcherConfig:
    """全局配置单例。"""
    return ResearcherConfig()
