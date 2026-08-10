# -*- coding: utf-8 -*-
"""DSA 工具层 — 封装 1.94.7.13 的 7 个核心 API + 6 个新增分析工具。

工具列表：
  7 个核心 API（market_tools.py）：
    get_market_overview     /api/stock-analysis
    get_top_stocks          /api/top-20-stocks
    get_stock_detail        /api/stock-info?query=X
    get_hot_industries      /api/top-limit-up-industries
    get_industry_limitup    /api/industry-limit-up?industry=X
    get_indexes             /api/market-indexes
    get_history_analysis    /api/stock-analysis-by-date?date=X

  6 个新增分析工具（new_tools.py）：
    get_bollinger           布林线通道（日线，自算 fallback）
    get_fundamentals        基本面指标（PE/PB/股息率/ROE/基金持仓）
    get_vix                 VIX 恐慌指数
    mainline_alert          新主线预警（空头→多头行业检测）
    get_industry_deviation  行业偏离度
    get_wall_street         华尔街机构观点
"""

from .market_tools import (
    get_market_overview,
    get_top_stocks,
    get_stock_detail,
    get_hot_industries,
    get_industry_limitup,
    get_indexes,
    get_history_analysis,
    BASE_URL,
    DEFAULT_TIMEOUT,
)

from .new_tools import (
    get_bollinger,
    get_fundamentals,
    get_vix,
    mainline_alert,
    get_industry_deviation,
    get_wall_street,
)

__all__ = [
    # 核心 API
    "get_market_overview",
    "get_top_stocks",
    "get_stock_detail",
    "get_hot_industries",
    "get_industry_limitup",
    "get_indexes",
    "get_history_analysis",
    # 新增工具
    "get_bollinger",
    "get_fundamentals",
    "get_vix",
    "mainline_alert",
    "get_industry_deviation",
    "get_wall_street",
    # 配置
    "BASE_URL",
    "DEFAULT_TIMEOUT",
]
__version__ = "0.2.0"
