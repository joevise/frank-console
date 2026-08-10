# -*- coding: utf-8 -*-
"""
数据采集层 — 封装 DSA 的 DataFetcherManager。

底层多源降级：Tushare → Efinance → AkShare → Baostock → YFinance
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_manager():
    """获取 DataFetcherManager 单例（带多源降级）。"""
    import sys
    import os

    # 找到 data_provider_src 目录
    _src = os.path.join(os.path.dirname(__file__), "..", "data_provider_src")
    _src = os.path.abspath(_src)
    if _src not in sys.path:
        sys.path.insert(0, _src)

    # data_provider_src 内部 import 用的是 `data_provider.xxx`
    # 把 data_provider_src 的父目录也加入 path
    _parent = os.path.dirname(_src)
    if _parent not in sys.path:
        sys.path.insert(0, _parent)

    # data_provider_src 目录改名为 data_provider 可访问
    # 通过创建 alias
    import importlib
    if "data_provider" not in sys.modules:
        # data_provider_src → data_provider
        _mod = importlib.import_module("data_provider_src")
        sys.modules["data_provider"] = _mod
        # 子模块
        for sub in ["base", "tushare_fetcher", "akshare_fetcher",
                     "efinance_fetcher", "baostock_fetcher",
                     "yfinance_fetcher", "pytdx_fetcher",
                     "tencent_fetcher", "longbridge_fetcher",
                     "finnhub_fetcher", "alphavantage_fetcher",
                     "fundamental_adapter", "realtime_types",
                     "us_index_mapping", "tw_institutional_fetcher",
                     "yfinance_fundamental_adapter"]:
            try:
                importlib.import_module(f"data_provider_src.{sub}")
                sys.modules[f"data_provider.{sub}"] = sys.modules[
                    f"data_provider_src.{sub}"
                ]
            except Exception:
                pass

    from data_provider_src.base import DataFetcherManager
    return DataFetcherManager()


def _safe_call(func, *args, **kwargs) -> Dict[str, Any]:
    """安全调用：异常不 crash，返回 error dict。"""
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        logger.warning("%s failed: %s", getattr(func, "__name__", "call"), exc)
        return {"status": "error", "error": str(exc)}


# ============================================================
# 数据工具函数
# ============================================================

def get_daily_history(stock_code: str, days: int = 60) -> Dict[str, Any]:
    """获取日K线历史数据。

    Args:
        stock_code: 股票代码，如 '600519'
        days: 天数，默认 60

    Returns:
        dict: K线数据 + 元数据
    """
    manager = _get_manager()
    return _safe_call(
        manager.get_daily_data, stock_code=stock_code, days=days
    )


def get_realtime_quote(stock_code: str) -> Dict[str, Any]:
    """获取实时行情快照。

    Args:
        stock_code: 股票代码

    Returns:
        dict: 当前价/涨跌幅/成交量/买卖盘等
    """
    manager = _get_manager()
    return _safe_call(manager.get_realtime_quote, stock_code=stock_code)


def get_stock_info(stock_code: str) -> Dict[str, Any]:
    """获取基本面信息（PE/PB/ROE/市值/财报摘要）。

    Args:
        stock_code: 股票代码

    Returns:
        dict: 基本面数据
    """
    manager = _get_manager()
    return _safe_call(manager.get_stock_fundamental, stock_code=stock_code)


def get_chip_distribution(stock_code: str) -> Dict[str, Any]:
    """获取筹码分布数据。

    Args:
        stock_code: 股票代码

    Returns:
        dict: 90%集中度/获利比例/平均成本/筹码峰
    """
    manager = _get_manager()
    return _safe_call(manager.get_chip_distribution, stock_code=stock_code)


def get_capital_flow(stock_code: str) -> Dict[str, Any]:
    """获取主力资金流向数据（仅 A 股）。

    Args:
        stock_code: A 股代码

    Returns:
        dict: 主力净流入/5日/10日累计 + 板块资金排行
    """
    manager = _get_manager()
    return _safe_call(manager.get_capital_flow_context, stock_code=stock_code)


def get_market_indices(region: str = "cn") -> List[Dict[str, Any]]:
    """获取大盘指数。

    Args:
        region: 'cn' / 'hk' / 'us'

    Returns:
        list: 各指数当前数据
    """
    manager = _get_manager()
    result = _safe_call(manager.get_main_indices, region=region)
    if isinstance(result, dict) and "error" in result:
        return result
    return result or []


def get_sector_rankings(top_n: int = 10) -> Dict[str, Any]:
    """获取板块/概念排行。

    Args:
        top_n: 返回前 N 个

    Returns:
        dict: {'industries': [...], 'concepts': [...]}
    """
    manager = _get_manager()
    industries = _safe_call(manager.get_sector_rankings, n=top_n)
    concepts = _safe_call(manager.get_concept_rankings, n=top_n)

    result = {"industries": [], "concepts": []}

    if industries and not (isinstance(industries, dict) and "error" in industries):
        # DataFetcherManager.get_sector_rankings 返回 (industry_list, concept_list)
        if isinstance(industries, tuple) and len(industries) >= 1:
            result["industries"] = industries[0] or []
        elif isinstance(industries, list):
            result["industries"] = industries

    if concepts and not (isinstance(concepts, dict) and "error" in concepts):
        if isinstance(concepts, tuple) and len(concepts) >= 2:
            result["concepts"] = concepts[1] or []
        elif isinstance(concepts, list):
            result["concepts"] = concepts

    return result
