# -*- coding: utf-8 -*-
"""
ResearcherAPI — Frank 调用 dsa_researcher 的统一入口。

五组能力：
  get_data()    — 数据采集（K线/行情/基本面/筹码/资金流/板块）
  analyze()     — 技术计算（趋势/均线/量价/形态）
  search()      — 情报搜索（新闻/公告/风险信号）
  advise()      — 投资顾问（7条铁律 + 16套策略 → 综合建议）
  full_report() — 一站式全量报告
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .config import ResearcherConfig, get_config

logger = logging.getLogger(__name__)


class ResearcherAPI:
    """Frank 的研究员工具包。

    用法：
        api = ResearcherAPI(tushare_token="xxx")
        report = api.full_report("600519", "贵州茅台")
    """

    def __init__(
        self,
        tushare_token: Optional[str] = None,
        openrouter_key: Optional[str] = None,
        primary_model: str = "xiaomi/mimo-v2.5",
        fallback_model: str = "deepseek/deepseek-v4-flash",
    ):
        """初始化。

        Args:
            tushare_token: Tushare API token。不传则从环境变量 TUSHARE_TOKEN 读。
            openrouter_key: OpenRouter API key。不传则从环境变量 OPENROUTER_API_KEY 读。
            primary_model: 主 LLM 模型（默认 xiaomi/mimo-v2.5）
            fallback_model: 备用模型（默认 deepseek/deepseek-v4-flash）
        """
        self.config = ResearcherConfig(
            tushare_token=tushare_token,
            openrouter_key=openrouter_key,
            primary_model=primary_model,
            fallback_model=fallback_model,
        )

    # ========================================================
    # 1. 数据采集层
    # ========================================================

    def get_data(self, stock_code: str, days: int = 60) -> Dict[str, Any]:
        """一站式数据采集。

        Returns:
            dict: {
                'history': K线数据,
                'quote': 实时行情,
                'info': 基本面,
                'chip': 筹码分布,
                'capital_flow': 资金流向,
            }
        """
        from .data.fetcher import (
            get_daily_history,
            get_realtime_quote,
            get_stock_info,
            get_chip_distribution,
            get_capital_flow,
        )

        return {
            "history": get_daily_history(stock_code, days=days),
            "quote": get_realtime_quote(stock_code),
            "info": get_stock_info(stock_code),
            "chip": get_chip_distribution(stock_code),
            "capital_flow": get_capital_flow(stock_code),
        }

    def get_market(self, top_n: int = 10, region: str = "cn") -> Dict[str, Any]:
        """获取市场概览（大盘指数 + 板块排行）。"""
        from .data.fetcher import get_market_indices, get_sector_rankings

        return {
            "indices": get_market_indices(region=region),
            "sectors": get_sector_rankings(top_n=top_n),
        }

    # ========================================================
    # 2. 技术计算层
    # ========================================================

    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """一站式技术分析。

        Returns:
            dict: {
                'trend': 趋势分析(MA/MACD/RSI/乖离率/信号),
                'volume': 量价分析,
                'pattern': K线形态,
                'ma_detail': 详细均线数据,
            }
        """
        from .analysis.trend import analyze_trend, calculate_ma
        from .analysis.volume import get_volume_analysis
        from .analysis.pattern import analyze_pattern

        return {
            "trend": analyze_trend(stock_code),
            "volume": get_volume_analysis(stock_code),
            "pattern": analyze_pattern(stock_code),
            "ma_detail": calculate_ma(stock_code),
        }

    # ========================================================
    # 3. 情报搜索层
    # ========================================================

    def search(self, stock_code: str, stock_name: str = "") -> Dict[str, Any]:
        """新闻 + 公告 + 综合情报 + 风险信号扫描。"""
        from .data.search import search_comprehensive_intel

        return search_comprehensive_intel(stock_code, stock_name)

    # ========================================================
    # 4. 投资顾问层
    # ========================================================

    def advise(
        self,
        stock_code: str,
        stock_name: str = "",
        analysis: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """投资顾问建议。

        自动整合技术分析 + 风险排查 + 铁律检查 + 策略匹配。

        Returns:
            dict: {
                'rules_check': 7条铁律逐条检查,
                'strategy_matches': 最匹配的策略,
                'advisor_opinion': 综合文字建议,
                'risk_flags': 风险标记,
                'overall_status': bullish/bearish/neutral/danger
            }
        """
        from .advisor.advisor import advise

        chip_data = data.get("chip") if data else None
        stock_info = data.get("info") if data else None

        return advise(
            stock_code=stock_code,
            stock_name=stock_name,
            analysis=analysis.get("trend") if analysis else None,
            chip_data=chip_data,
            stock_info=stock_info,
            openrouter_key=self.config.openrouter_key,
            primary_model=self.config.primary_model,
            fallback_model=self.config.fallback_model,
        )

    # ========================================================
    # 5. 全量报告（一站式）
    # ========================================================

    def full_report(
        self,
        stock_code: str,
        stock_name: str = "",
        days: int = 60,
    ) -> Dict[str, Any]:
        """全量研究报告 = 数据 + 分析 + 搜索 + 顾问建议。

        这是 Frank 最常用的入口：一句话拿到所有信息。

        Returns:
            dict: {
                'stock_code': str,
                'stock_name': str,
                'data': {...},        # 数据层
                'analysis': {...},    # 计算层
                'intel': {...},       # 搜索层
                'advisor': {...},     # 顾问层
            }
        """
        logger.info("开始生成 %s(%s) 全量报告...", stock_code, stock_name)

        # 1. 数据
        data = self.get_data(stock_code, days=days)

        # 2. 分析
        analysis = self.analyze(stock_code)

        # 3. 搜索
        intel = self.search(stock_code, stock_name)

        # 4. 顾问
        advisor = self.advise(
            stock_code, stock_name,
            analysis=analysis,
            data=data,
        )

        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "data": data,
            "analysis": analysis,
            "intel": intel,
            "advisor": advisor,
        }
