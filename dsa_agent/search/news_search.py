"""新闻搜索（Bocha 搜索 API，国内支持好）。"""
from __future__ import annotations
import logging
from typing import Any, Dict, List
import requests
from ..core.config import get_settings

logger = logging.getLogger(__name__)
BOCHA_URL = "https://api.bochaai.com/v1/web-search"


def search_news(query: str, max_results: int = 5, freshness: str = "oneDay") -> Dict[str, Any]:
    """搜索新闻，返回标题+摘要+链接列表。

    Args:
        query: 搜索关键词
        max_results: 最大结果数
        freshness: 时效性（oneDay/oneWeek/oneMonth/noLimit）
    """
    settings = get_settings()
    if not settings.BOCHA_API_KEY:
        return {"success": False, "error": "BOCHA_API_KEY not configured", "results": []}

    headers = {
        "Authorization": f"Bearer {settings.BOCHA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "freshness": freshness,
        "summary": True,
        "count": max_results,
    }

    try:
        resp = requests.post(BOCHA_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        d = resp.json()

        results = []
        # Bocha 返回格式可能有变化，兼容处理
        web_pages = d.get("data", {}).get("webPages", {}).get("value", [])
        if not web_pages:
            web_pages = d.get("results", [])
        if not web_pages and isinstance(d.get("data"), list):
            web_pages = d["data"]

        for item in web_pages[:max_results]:
            results.append({
                "title": item.get("name", item.get("title", "")),
                "snippet": item.get("snippet", item.get("summary", "")),
                "url": item.get("url", item.get("link", "")),
                "source": item.get("siteName", item.get("source", "")),
                "date": item.get("dateLastCrawled", item.get("date", "")),
            })

        return {"success": True, "results": results, "count": len(results)}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Bocha 搜索超时", "results": []}
    except Exception as exc:
        logger.warning("bocha search failed: %s", exc)
        return {"success": False, "error": str(exc), "results": []}


def search_stock_news(stock_name: str, industry: str = "") -> Dict[str, Any]:
    """搜索个股相关新闻（自动组合关键词）。"""
    results = []

    # 搜个股新闻
    r1 = search_news(f"{stock_name} 股票 最新", max_results=3, freshness="oneWeek")
    if r1.get("success"):
        results.extend(r1["results"])

    # 搜行业新闻（如果有行业）
    if industry:
        r2 = search_news(f"{industry} 行业 板块 最新", max_results=2, freshness="oneWeek")
        if r2.get("success"):
            results.extend(r2["results"])

    return {"success": True, "results": results, "count": len(results)}
