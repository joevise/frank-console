# -*- coding: utf-8 -*-
"""
趋势分析 — 均线/MACD/RSI/乖离率/买卖信号。

从 DSA 的 StockTrendAnalyzer 抽取核心计算逻辑，用 pandas 独立实现，
不依赖 DSA 的数据库/service 层。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _load_df(stock_code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """从 data_provider 拉 K 线，返回 DataFrame。"""
    from ..data.fetcher import _get_manager

    manager = _get_manager()
    raw = manager.get_daily_data(stock_code=stock_code, days=days)

    if not raw or isinstance(raw, dict) and raw.get("error"):
        return None

    # DSA get_daily_data 返回格式：{code, data: [{date, open, high, low, close, volume}]}
    bars = None
    if isinstance(raw, dict):
        bars = raw.get("data") or raw.get("bars") or raw.get("klines")
    elif isinstance(raw, list):
        bars = raw

    if not bars or not isinstance(bars, list):
        return None

    df = pd.DataFrame(bars)
    # 标准列名
    for col in ["date", "open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            return None

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["close"])

    return df


def analyze_trend(stock_code: str) -> Dict[str, Any]:
    """综合技术趋势分析。

    Returns:
        dict: MA排列/乖离率/MACD/RSI/量能/支撑压力位/买卖信号/评分
    """
    df = _load_df(stock_code, days=60)
    if df is None or df.empty:
        return {"error": f"无法获取 {stock_code} 的历史数据"}
    if len(df) < 20:
        return {"error": f"{stock_code} 数据不足（{len(df)}天），需要至少20天"}

    close = df["close"]
    volume = df["volume"]
    current = float(close.iloc[-1])

    # ---- 均线 ----
    ma5 = float(close.rolling(5).mean().iloc[-1])
    ma10 = float(close.rolling(10).mean().iloc[-1])
    ma20 = float(close.rolling(20).mean().iloc[-1])
    ma60 = float(close.rolling(60).mean().iloc[-1]) if len(close) >= 60 else None

    # 均线排列
    if ma5 > ma10 > ma20:
        ma_alignment = "多头排列"
    elif ma5 < ma10 < ma20:
        ma_alignment = "空头排列"
    else:
        ma_alignment = "交叉/混合"

    # 趋势强度
    trend_strength = abs((current - ma20) / ma20 * 100) if ma20 else 0

    # ---- 乖离率 ----
    bias_ma5 = (current - ma5) / ma5 * 100 if ma5 else 0
    bias_ma10 = (current - ma10) / ma10 * 100 if ma10 else 0
    bias_ma20 = (current - ma20) / ma20 * 100 if ma20 else 0

    # ---- MACD ----
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd_bar = (dif - dea) * 2

    macd_dif = float(dif.iloc[-1])
    macd_dea = float(dea.iloc[-1])
    macd_bar_val = float(macd_bar.iloc[-1])

    if macd_dif > macd_dea and macd_dif > 0:
        macd_status = "金叉多头"
        macd_signal = "MACD 金叉且在零轴上方，多头强势"
    elif macd_dif > macd_dea:
        macd_status = "金叉"
        macd_signal = "MACD 金叉，偏多"
    elif macd_dif < macd_dea and macd_dif < 0:
        macd_status = "死叉空头"
        macd_signal = "MACD 死叉且在零轴下方，空头强势"
    else:
        macd_status = "死叉"
        macd_signal = "MACD 死叉，偏空"

    # ---- RSI ----
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain_6 = gain.rolling(6).mean()
    avg_loss_6 = loss.rolling(6).mean()
    rs_6 = avg_gain_6 / avg_loss_6.replace(0, np.nan)
    rsi_6 = float((100 - (100 / (1 + rs_6))).iloc[-1]) if not avg_loss_6.iloc[-1] or avg_loss_6.iloc[-1] == 0 else 50.0

    avg_gain_12 = gain.rolling(12).mean()
    avg_loss_12 = loss.rolling(12).mean()
    rs_12 = avg_gain_12 / avg_loss_12.replace(0, np.nan)
    rsi_12 = float((100 - (100 / (1 + rs_12))).fillna(50).iloc[-1])

    rsi_status = "超买" if rsi_6 > 80 else "超卖" if rsi_6 < 20 else "中性"

    # ---- 量能 ----
    avg_vol_5 = float(volume.tail(5).mean())
    avg_vol_20 = float(volume.tail(20).mean()) if len(volume) >= 20 else avg_vol_5
    latest_vol = float(volume.iloc[-1])
    vol_ratio_5d = latest_vol / avg_vol_5 if avg_vol_5 > 0 else 1.0

    if vol_ratio_5d > 1.5:
        volume_status = "放量"
    elif vol_ratio_5d < 0.6:
        volume_status = "缩量"
    else:
        volume_status = "正常"

    # ---- 支撑压力位 ----
    recent = df.tail(20)
    resistance_levels = [float(x) for x in sorted(recent["high"].nlargest(3).tolist(), reverse=True)]
    support_levels = [float(x) for x in sorted(recent["low"].nsmallest(3).tolist())]

    # ---- 买卖信号 ----
    signal_score = 50  # 基准
    signal_reasons = []

    if ma_alignment == "多头排列":
        signal_score += 15
        signal_reasons.append("✅ 多头排列：MA5 > MA10 > MA20")
    elif ma_alignment == "空头排列":
        signal_score -= 15
        signal_reasons.append("❌ 空头排列")

    if abs(bias_ma5) < 2:
        signal_score += 10
        signal_reasons.append("✅ 低乖离率：<2%，最佳买点区间")
    elif bias_ma5 > 5:
        signal_score -= 15
        signal_reasons.append(f"⚠️ 乖离率 {bias_ma5:.1f}%，追高风险")
    elif bias_ma5 > 2:
        signal_score -= 5
        signal_reasons.append(f"⚠️ 乖离率 {bias_ma5:.1f}%，偏高")

    if macd_status.startswith("金叉"):
        signal_score += 10
        signal_reasons.append(f"✅ {macd_signal}")
    else:
        signal_score -= 5
        signal_reasons.append(f"⚠️ {macd_signal}")

    if volume_status == "放量":
        signal_score += 5
        signal_reasons.append("✅ 量能放大")

    if rsi_6 > 80:
        signal_score -= 10
        signal_reasons.append("⚠️ RSI 超买")
    elif rsi_6 < 20:
        signal_score += 10
        signal_reasons.append("✅ RSI 超卖，反弹机会")

    signal_score = max(0, min(100, signal_score))

    if signal_score >= 70:
        buy_signal = "买入"
    elif signal_score >= 55:
        buy_signal = "谨慎买入"
    elif signal_score >= 45:
        buy_signal = "观望"
    elif signal_score >= 30:
        buy_signal = "谨慎卖出"
    else:
        buy_signal = "卖出"

    return {
        "code": stock_code,
        "current_price": round(current, 2),
        "trend_status": ma_alignment,
        "ma_alignment": ma_alignment,
        "trend_strength": round(trend_strength, 2),
        "ma5": round(ma5, 2),
        "ma10": round(ma10, 2),
        "ma20": round(ma20, 2),
        "ma60": round(ma60, 2) if ma60 else None,
        "bias_ma5": round(bias_ma5, 2),
        "bias_ma10": round(bias_ma10, 2),
        "bias_ma20": round(bias_ma20, 2),
        "macd_dif": round(macd_dif, 4),
        "macd_dea": round(macd_dea, 4),
        "macd_bar": round(macd_bar_val, 4),
        "macd_status": macd_status,
        "macd_signal": macd_signal,
        "rsi_6": round(rsi_6, 2),
        "rsi_12": round(rsi_12, 2),
        "rsi_status": rsi_status,
        "volume_status": volume_status,
        "volume_ratio_5d": round(vol_ratio_5d, 2),
        "support_ma5": current > ma5 if ma5 else False,
        "support_ma10": current > ma10 if ma10 else False,
        "resistance_levels": resistance_levels,
        "support_levels": support_levels,
        "buy_signal": buy_signal,
        "signal_score": signal_score,
        "signal_reasons": signal_reasons,
    }


def calculate_ma(stock_code: str, periods: Optional[str] = None, days: int = 120) -> Dict[str, Any]:
    """计算任意周期均线。

    Args:
        stock_code: 股票代码
        periods: 逗号分隔的周期，如 '5,10,20,60'，默认 '5,10,20,30,60,120,250'
        days: 拉取的天数

    Returns:
        dict: 每条均线的值/乖离率/价格在上方与否 + 整体排列判断
    """
    df = _load_df(stock_code, days=days)
    if df is None or df.empty:
        return {"error": f"无法获取 {stock_code} 的历史数据"}

    close = df["close"]
    current = float(close.iloc[-1])

    default_periods = [5, 10, 20, 30, 60, 120, 250]
    if periods:
        try:
            period_list = sorted(set(int(p.strip()) for p in periods.split(",") if p.strip().isdigit()))
        except Exception:
            period_list = default_periods
    else:
        period_list = default_periods

    result = {
        "code": stock_code,
        "current_price": round(current, 2),
        "data_points": len(df),
        "ma": {},
    }

    for period in period_list:
        if len(close) < period:
            result["ma"][f"ma{period}"] = None
            continue
        ma_val = float(close.rolling(period).mean().iloc[-1])
        bias = (current - ma_val) / ma_val * 100 if ma_val else None
        result["ma"][f"ma{period}"] = {
            "value": round(ma_val, 2),
            "bias_pct": round(bias, 2) if bias is not None else None,
            "price_above": current > ma_val,
        }

    ma_values = [v for v in result["ma"].values() if v is not None]
    above_count = sum(1 for v in ma_values if v["price_above"])
    result["above_ma_count"] = above_count
    result["total_ma_count"] = len(ma_values)
    result["ma_alignment"] = (
        "多头排列" if above_count == len(ma_values)
        else "空头排列" if above_count == 0
        else f"混合({above_count}/{len(ma_values)}条均线上方)"
    )
    return result
