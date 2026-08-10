# -*- coding: utf-8 -*-
"""量价分析 — 从 DSA analysis_tools 抽取，纯 pandas 实现。"""

from __future__ import annotations

import logging
from typing import Any, Dict

import pandas as pd

from .trend import _load_df

logger = logging.getLogger(__name__)


def get_volume_analysis(stock_code: str, days: int = 30) -> Dict[str, Any]:
    """量价关系分析。

    Returns:
        dict: 量比/涨跌日成交量对比/量价配合度/形态判断
    """
    df = _load_df(stock_code, days=max(days + 20, 60))
    if df is None or df.empty:
        return {"error": f"无法获取 {stock_code} 的历史数据"}

    df = df.tail(days).copy()
    if len(df) < 5:
        return {"error": f"数据不足（{len(df)}天），需要至少5天"}

    close = df["close"]
    volume = df["volume"]

    avg_vol_5 = float(volume.tail(5).mean())
    avg_vol_10 = float(volume.tail(10).mean())
    avg_vol_20 = float(volume.tail(20).mean()) if len(df) >= 20 else avg_vol_10
    latest_vol = float(volume.iloc[-1])

    vol_ratio_5d = latest_vol / avg_vol_5 if avg_vol_5 > 0 else None
    vol_ratio_20d = latest_vol / avg_vol_20 if avg_vol_20 > 0 else None

    price_up = close.diff() > 0
    up_days = df[price_up]
    down_days = df[~price_up]

    avg_up_vol = float(up_days["volume"].mean()) if len(up_days) > 0 else 0
    avg_down_vol = float(down_days["volume"].mean()) if len(down_days) > 0 else 0

    # 量能趋势
    if len(volume) >= 10:
        recent_5 = float(volume.tail(5).mean())
        prior_5 = float(volume.iloc[-10:-5].mean())
        vol_trend_pct = (recent_5 - prior_5) / prior_5 * 100 if prior_5 > 0 else 0
        vol_trend = "放量" if vol_trend_pct > 20 else "缩量" if vol_trend_pct < -20 else "量能平稳"
    else:
        vol_trend_pct = 0
        vol_trend = "数据不足"

    high_vol_days = int((volume > avg_vol_20 * 2).sum()) if avg_vol_20 > 0 else 0

    # 量价形态判断
    if avg_up_vol > avg_down_vol * 1.3:
        pattern = "量价配合良好（上涨放量、下跌缩量）"
    elif avg_down_vol > avg_up_vol * 1.3:
        pattern = "量价背离（下跌放量、上涨缩量，偏空）"
    elif vol_ratio_5d and vol_ratio_5d > 1.5:
        pattern = "近期明显放量"
    elif vol_ratio_5d and vol_ratio_5d < 0.6:
        pattern = "近期明显缩量"
    else:
        pattern = "量价关系中性"

    return {
        "code": stock_code,
        "period_days": len(df),
        "latest_volume": latest_vol,
        "avg_volume_5d": round(avg_vol_5, 0),
        "avg_volume_20d": round(avg_vol_20, 0),
        "volume_ratio_vs_5d": round(vol_ratio_5d, 2) if vol_ratio_5d else None,
        "volume_ratio_vs_20d": round(vol_ratio_20d, 2) if vol_ratio_20d else None,
        "avg_up_day_volume": round(avg_up_vol, 0),
        "avg_down_day_volume": round(avg_down_vol, 0),
        "volume_trend": vol_trend,
        "volume_trend_pct": round(vol_trend_pct, 1),
        "high_volume_days": high_vol_days,
        "pattern": pattern,
    }
