# -*- coding: utf-8 -*-
"""
搜索层 — 新闻/公告/情报搜索。

DSA 原版的搜索依赖 intelligence_service + 数据库（SQLite 落盘缓存）。
本包做了轻量化：优先用 fetcher 内置的新闻接口；如果不可用则走 web search。
保持接口签名一致，Frank 调用时无感知。
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def search_stock_news(stock_code: str, stock_name: str = "") -> Dict[str, Any]:
    """搜索个股相关新闻和公告。

    Args:
        stock_code: 股票代码，如 '600519'
        stock_name: 股票名称，如 '贵州茅台'（可选，提高搜索精度）

    Returns:
        dict: {
            'stock_code': str,
            'stock_name': str,
            'news': [{'title', 'source', 'date', 'url', 'summary'}],
            'status': 'ok' / 'degraded' / 'error'
        }
    """
    # 尝试用 fetcher manager 内置的新闻能力
    try:
        from .fetcher import _get_manager

        manager = _get_manager()
        # 部分 fetcher 有 news 方法
        for fetcher_name in ["EfinanceFetcher", "AkshareFetcher", "TushareFetcher"]:
            try:
                fetcher = manager._fetchers.get(fetcher_name)
                if fetcher and hasattr(fetcher, "search_news"):
                    news = fetcher.search_news(stock_code, stock_name)
                    if news:
                        return {
                            "stock_code": stock_code,
                            "stock_name": stock_name,
                            "news": news,
                            "source": fetcher_name,
                            "status": "ok",
                        }
            except Exception:
                continue
    except Exception as exc:
        logger.debug("fetcher news fallback failed: %s", exc)

    # Fallback: 返回占位结构，调用方可以用 web_search 补充
    return {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "news": [],
        "status": "degraded",
        "note": "内置新闻源不可用，建议使用 web_search 获取最新新闻",
    }


def search_comprehensive_intel(stock_code: str, stock_name: str = "") -> Dict[str, Any]:
    """综合情报搜索（新闻 + 公告 + 行业动态 + 舆情）。

    Args:
        stock_code: 股票代码
        stock_name: 股票名称

    Returns:
        dict: {
            'stock_code': str,
            'stock_name': str,
            'news': [...],
            'announcements': [...],
            'industry_trends': [...],
            'risk_flags': [...],
            'status': str
        }
    """
    base = search_stock_news(stock_code, stock_name)

    # 尝试获取更多维度的情报
    result = {
        "stock_code": stock_code,
        "stock_name": stock_name,
        "news": base.get("news", []),
        "announcements": [],
        "industry_trends": [],
        "risk_flags": [],
        "status": base.get("status", "degraded"),
    }

    # 基础风险关键词扫描
    risk_keywords = ["减持", "预亏", "亏损", "监管", "处罚", "解禁",
                     "退市", "问询", "立案", "违规"]
    for item in base.get("news", []):
        title = (item.get("title", "") + item.get("summary", "")).lower()
        for kw in risk_keywords:
            if kw in title:
                result["risk_flags"].append({
                    "keyword": kw,
                    "source": item.get("title", ""),
                    "date": item.get("date", ""),
                })
                break

    return result
