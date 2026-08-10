# -*- coding: utf-8 -*-
"""每日分析定时任务 — 用 APScheduler 每天定时跑一遍全量用户的自选列表分析。"""

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models.models import User
from app.api.reports import _run_analysis_for_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


def run_daily_analysis_all_users():
    """对所有活跃用户跑一遍每日分析。"""
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        logger.info("开始每日分析任务，共 %d 个用户", len(users))
        for user in users:
            try:
                results = _run_analysis_for_user(user.id, db)
                logger.info("用户 %s 分析完成: %d 只股票", user.username, len(results))
            except Exception as exc:
                logger.exception("用户 %s 分析失败: %s", user.username, exc)
    finally:
        db.close()


def main():
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        run_daily_analysis_all_users,
        trigger=CronTrigger(
            hour=settings.daily_analysis_cron_hour,
            minute=settings.daily_analysis_cron_minute,
        ),
        id="daily_analysis",
        replace_existing=True,
    )
    logger.info(
        "定时任务已启动，每天 %02d:%02d 跑每日分析",
        settings.daily_analysis_cron_hour,
        settings.daily_analysis_cron_minute,
    )
    scheduler.start()


if __name__ == "__main__":
    main()
