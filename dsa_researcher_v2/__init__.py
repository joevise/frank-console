# -*- coding: utf-8 -*-
"""
DSA Researcher — 从 daily_stock_analysis 抽取的 A 股研究工具包。

三层能力：
  1. 数据层（data）   — K线/行情/基本面/筹码/资金流/板块
  2. 计算层（analysis）— 均线/MACD/乖离率/量价/K线形态
  3. 顾问层（advisor）— 7条铁律 + 16套策略框架

Frank（或其他 Agent）通过 ResearcherAPI 调用。
"""

from .api import ResearcherAPI

__all__ = ["ResearcherAPI"]
__version__ = "0.1.0"
