# -*- coding: utf-8 -*-
"""
LLM 调用层 — 通过 OpenRouter 调用 LLM，用于策略分析。

主模型：xiaomi/mimo-v2.5
fallback：deepseek/deepseek-v4-flash
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# 默认模型配置
DEFAULT_PRIMARY_MODEL = "xiaomi/mimo-v2.5"
DEFAULT_FALLBACK_MODEL = "deepseek/deepseek-v4-flash"

DEFAULT_OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def call_llm(
    messages: List[Dict[str, str]],
    api_key: Optional[str] = None,
    primary_model: str = DEFAULT_PRIMARY_MODEL,
    fallback_model: str = DEFAULT_FALLBACK_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 2000,
    timeout: int = 60,
) -> str:
    """调用 LLM（主模型失败自动 fallback）。

    Args:
        messages: OpenAI 格式的消息列表
        api_key: OpenRouter API key（不传则从环境变量读）
        primary_model: 主模型
        fallback_model: 备用模型
        temperature: 温度
        max_tokens: 最大输出 token
        timeout: 超时秒数

    Returns:
        str: LLM 回复文本
    """
    key = api_key or DEFAULT_OPENROUTER_KEY
    if not key:
        logger.warning("OpenRouter API key 未配置，LLM 调用跳过")
        return ""

    # 尝试主模型，失败则 fallback
    for model in [primary_model, fallback_model]:
        try:
            resp = requests.post(
                _OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info("LLM 调用成功: model=%s, tokens=%s", model,
                        data.get("usage", {}).get("total_tokens", "?"))
            return content
        except Exception as exc:
            logger.warning("LLM 调用失败 model=%s: %s", model, exc)
            if model == fallback_model:
                # 两个模型都挂了
                logger.error("主模型和备用模型都调用失败")
                return ""
            continue

    return ""


def analyze_with_strategy(
    strategy_name: str,
    strategy_instructions: str,
    stock_code: str,
    stock_name: str,
    analysis_data: Dict[str, Any],
    api_key: Optional[str] = None,
) -> str:
    """用指定策略的 instructions 分析一只股票。

    把策略框架 + 技术数据喂给 LLM，让它按策略逻辑出分析意见。

    Args:
        strategy_name: 策略名称（如 'chan_theory'）
        strategy_instructions: 策略 YAML 里的 instructions 自然语言
        stock_code: 股票代码
        stock_name: 股票名称
        analysis_data: analyze_trend + volume + pattern 的合并数据
        api_key: OpenRouter key

    Returns:
        str: LLM 的策略分析意见
    """
    import json as _json

    system_prompt = f"""你是一个 A 股交易策略分析专家。你正在使用「{strategy_name}」策略框架来分析股票。

策略框架说明：
{strategy_instructions}

请严格按照上述策略框架的逻辑来分析。输出要求：
1. 按策略框架的步骤逐一分析
2. 给出该策略视角下的结论（看多/看空/中性）
3. 指出关键信号和风险点
4. 给出评分建议（-20 到 +20，0 为中性）

用简洁的中文输出，不要废话。"""

    # 构建用户消息：把技术数据格式化喂进去
    data_summary = _format_analysis_for_llm(analysis_data, stock_code, stock_name)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": data_summary},
    ]

    return call_llm(messages, api_key=api_key, max_tokens=1500, temperature=0.3)


def _format_analysis_for_llm(
    analysis_data: Dict[str, Any],
    stock_code: str,
    stock_name: str,
) -> str:
    """把技术分析数据格式化成 LLM 能读的自然语言。"""
    parts = [f"股票：{stock_name}({stock_code})\n"]

    trend = analysis_data.get("trend", {})
    if trend:
        parts.append("【技术趋势】")
        parts.append(f"  当前价：{trend.get('current_price', 'N/A')}")
        parts.append(f"  均线排列：{trend.get('ma_alignment', 'N/A')}")
        parts.append(f"  MA5={trend.get('ma5')} MA10={trend.get('ma10')} MA20={trend.get('ma20')} MA60={trend.get('ma60')}")
        parts.append(f"  乖离率：MA5={trend.get('bias_ma5')}% MA10={trend.get('bias_ma10')}% MA20={trend.get('bias_ma20')}%")
        parts.append(f"  MACD：DIF={trend.get('macd_dif')} DEA={trend.get('macd_dea')} BAR={trend.get('macd_bar')} ({trend.get('macd_status')})")
        parts.append(f"  RSI：6日={trend.get('rsi_6')} 12日={trend.get('rsi_12')} ({trend.get('rsi_status')})")
        parts.append(f"  量能：{trend.get('volume_status')}（量比5日={trend.get('volume_ratio_5d')}）")
        parts.append(f"  信号评分：{trend.get('signal_score')}/100（{trend.get('buy_signal')}）")
        if trend.get("signal_reasons"):
            parts.append(f"  信号理由：{'；'.join(trend['signal_reasons'])}")
        parts.append("")

    volume = analysis_data.get("volume", {})
    if volume and "error" not in volume:
        parts.append("【量价分析】")
        parts.append(f"  {volume.get('pattern', '')}")
        parts.append(f"  量能趋势：{volume.get('volume_trend')}（{volume.get('volume_trend_pct')}%）")
        parts.append(f"  涨日均价量={volume.get('avg_up_day_volume')} 跌日均价量={volume.get('avg_down_day_volume')}")
        parts.append("")

    pattern = analysis_data.get("pattern", {})
    if pattern and "error" not in pattern:
        parts.append("【K线形态】")
        parts.append(f"  检测到 {pattern.get('patterns_count', 0)} 个形态：{pattern.get('summary', '无')}")
        if pattern.get("patterns"):
            for p in pattern["patterns"][:3]:
                parts.append(f"    - {p['pattern']}（{p['strength']}）：{p['desc']}")
        parts.append("")

    intel = analysis_data.get("intel", {})
    if intel:
        news = intel.get("news", [])
        if news:
            parts.append("【近期新闻（前5条）】")
            for n in news[:5]:
                parts.append(f"  - {n.get('date', '')} {n.get('title', '')}")
        risk = intel.get("risk_flags", [])
        if risk:
            parts.append(f"【风险信号】{', '.join(r.get('keyword', '') for r in risk[:5])}")
        parts.append("")

    parts.append("请按策略框架分析这只股票。")

    return "\n".join(parts)
