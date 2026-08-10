"""Tushare HTTP API 客户端（直接 POST，不依赖 tushare 包）。"""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
import requests
from ..core.config import get_settings

logger = logging.getLogger(__name__)
TUSHARE_URL = "https://api.tushare.pro"


def _call_tushare(api_name: str, params: dict, fields: str = "") -> Dict[str, Any]:
    """调用 Tushare HTTP API，返回标准化结果。"""
    settings = get_settings()
    payload = {"api_name": api_name, "token": settings.TUSHARE_TOKEN, "params": params, "fields": fields}
    try:
        resp = requests.post(TUSHARE_URL, json=payload, timeout=settings.REQUEST_TIMEOUT)
        resp.raise_for_status()
        d = resp.json()
        if d.get("code") != 0:
            return {"success": False, "error": d.get("msg", "unknown error"), "data": []}
        data = d.get("data", {})
        fields_list = data.get("fields", [])
        items = data.get("items", [])
        rows = [dict(zip(fields_list, row)) for row in items]
        return {"success": True, "data": rows, "count": len(rows)}
    except Exception as exc:
        logger.warning("tushare %s failed: %s", api_name, exc)
        return {"success": False, "error": str(exc), "data": []}


def convert_code(stock_code: str) -> str:
    """把 '600519' 转成 '600519.SH' 格式。"""
    code = stock_code.strip().upper()
    if "." in code:
        return code
    if code.startswith("6"):
        return f"{code}.SH"
    return f"{code}.SZ"


def get_daily(stock_code: str, limit: int = 60) -> Dict[str, Any]:
    """获取日K线（OHLCV）。"""
    ts_code = convert_code(stock_code)
    return _call_tushare("daily", {"ts_code": ts_code, "limit": limit},
                         "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount")


def get_daily_basic(stock_code: str, limit: int = 5) -> Dict[str, Any]:
    """获取每日指标（PE/PB/股息率/换手率/总市值）。"""
    ts_code = convert_code(stock_code)
    return _call_tushare("daily_basic", {"ts_code": ts_code, "limit": limit},
                         "ts_code,trade_date,close,turnover_rate,pe_ttm,pb,ps_ttm,dv_ratio,total_mv")


def get_stk_mins(stock_code: str, freq: str = "1min", limit: int = 60) -> Dict[str, Any]:
    """获取分钟K线。freq: 1min/5min/15min/30min/60min。"""
    ts_code = convert_code(stock_code)
    return _call_tushare("stk_mins", {"ts_code": ts_code, "freq": freq, "limit": limit})


def get_adj_factor(stock_code: str, limit: int = 60) -> Dict[str, Any]:
    """获取复权因子。"""
    ts_code = convert_code(stock_code)
    return _call_tushare("adj_factor", {"ts_code": ts_code, "limit": limit},
                         "ts_code,trade_date,adj_factor")


def get_stock_basic(stock_code: str) -> Dict[str, Any]:
    """获取股票基本信息（名称/行业/上市日期）。注意：限1次/小时。"""
    ts_code = convert_code(stock_code)
    return _call_tushare("stock_basic", {"ts_code": ts_code},
                         "ts_code,name,industry,market,list_date")


def get_index_daily(index_code: str, limit: int = 30) -> Dict[str, Any]:
    """获取指数日K线。指数代码: 000001.SH(上证), 399001.SZ(深证), 399006.SZ(创业板)。"""
    return _call_tushare("index_daily", {"ts_code": index_code, "limit": limit},
                         "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount")
