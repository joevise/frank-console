# -*- coding: utf-8 -*-
"""全局配置。"""

from __future__ import annotations

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库
    database_url: str = "postgresql://frank:frank_pw@postgres:5432/frank_console"
    redis_url: str = "redis://redis:6379/0"

    # JWT 认证
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7天

    # Frank 大脑 — OpenMind
    openmind_api_url: str = "https://openmind-backend.futurx.cc"
    openmind_mind_id: str = "019db41c-ca48-7d04-a94d-5d4ead5115c5"
    openmind_api_key: str = ""

    # Frank 大脑（LLM — 备用，OpenMind 不可用时降级）
    frank_llm_provider: str = "openrouter"
    frank_llm_api_key: str = ""
    frank_primary_model: str = "xiaomi/mimo-v2.5"
    frank_fallback_model: str = "deepseek/deepseek-v4-flash"
    frank_openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # dsa_researcher 顾问层（复用同一个 OpenRouter key）
    dsa_openrouter_key: str = ""
    dsa_tushare_token: str = ""

    # 每日分析定时任务
    daily_analysis_cron_hour: int = 9   # 每天9点跑
    daily_analysis_cron_minute: int = 30

    # CORS
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_prefix = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
