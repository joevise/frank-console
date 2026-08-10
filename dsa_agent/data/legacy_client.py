"""1.94.7.13 API 客户端（35信号/涨停/行业排名/打分）。"""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import quote
import requests
from ..core.config import get_settings

logger = logging.getLogger(__name__)


def _legacy_get(path: str, params: dict = None) -> Dict[str, Any]:
    settings = get_settings()
    url = f"{settings.LEGACY_API_URL}{path}"
    try:
        resp = requests.get(url, params=params, timeout=settings.REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("legacy %s failed: %s", path, exc)
        return {"error": str(exc)}


def get_market_overview() -> Dict[str, Any]:
    """多空分析+35信号行业排名。"""
    raw = _legacy_get("/api/stock-analysis")
    if "error" in raw:
        return {"success": False, "error": raw["error"]}
    return {"success": True, "data": raw}


def get_top_stocks() -> Dict[str, Any]:
    """打分最高20只股票。"""
    raw = _legacy_get("/api/top-20-stocks")
    if not raw.get("success"):
        return {"success": False, "error": raw.get("error", "unknown")}
    return {"success": True, "data": raw.get("data", [])}


def get_stock_detail(stock_code: str) -> Dict[str, Any]:
    """个股详情（140+字段）。"""
    raw = _legacy_get("/api/stock-info", {"query": stock_code})
    if not raw.get("success"):
        return {"success": False, "error": raw.get("error", "unknown")}
    return {"success": True, "data": raw.get("data", [])}


def get_hot_industries() -> Dict[str, Any]:
    """涨停数前5行业。"""
    raw = _legacy_get("/api/top-limit-up-industries")
    if not raw.get("success"):
        return {"success": False, "error": raw.get("error", "unknown")}
    return {"success": True, "data": raw.get("data", {})}


def get_industry_limitup(industry: str) -> Dict[str, Any]:
    """指定行业涨停股。自动URL encode中文。"""
    raw = _legacy_get("/api/industry-limit-up", {"industry": industry})
    if not raw.get("success"):
        return {"success": False, "error": raw.get("error", "unknown")}
    return {"success": True, "data": raw.get("data", {})}


def get_indexes() -> Dict[str, Any]:
    """三大指数实时。"""
    raw = _legacy_get("/api/market-indexes")
    if not raw.get("success"):
        return {"success": False, "error": raw.get("error", "unknown")}
    return {"success": True, "data": raw.get("data", {})}


def get_history_analysis(date: str) -> Dict[str, Any]:
    """历史多空分析（自动fallback最近有数据日期）。"""
    date_str = date.replace("-", "")
    for offset in range(8):
        try_date = (datetime.strptime(date_str, "%Y%m%d") - timedelta(days=offset)).strftime("%Y%m%d")
        raw = _legacy_get("/api/stock-analysis-by-date", {"date": try_date})
        if isinstance(raw, dict) and "error" not in raw:
            return {"success": True, "data": raw, "actual_date": try_date}
    # fallback: 用默认接口
    overview = get_market_overview()
    if overview.get("success"):
        return {"success": True, "data": overview["data"], "actual_date": "latest", "note": "fallback to latest"}
    return {"success": False, "error": "no data available"}
