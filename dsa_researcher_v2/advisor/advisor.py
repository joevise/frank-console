# -*- coding: utf-8 -*-
"""
投资顾问主入口 — 给一只股票，出综合顾问建议。

整合：7条铁律检查 + 策略匹配 + **LLM 策略分析** + 风险标记 + 综合意见。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .rules import check_rules
from .strategies import match_strategies

logger = logging.getLogger(__name__)


def advise(
    stock_code: str,
    stock_name: str = "",
    analysis: Optional[Dict[str, Any]] = None,
    chip_data: Optional[Dict[str, Any]] = None,
    intel_data: Optional[Dict[str, Any]] = None,
    stock_info: Optional[Dict[str, Any]] = None,
    volume_data: Optional[Dict[str, Any]] = None,
    pattern_data: Optional[Dict[str, Any]] = None,
    top_strategies: int = 3,
    openrouter_key: Optional[str] = None,
    primary_model: str = "xiaomi/mimo-v2.5",
    fallback_model: str = "deepseek/deepseek-v4-flash",
    enable_llm: bool = True,
) -> Dict[str, Any]:
    """投资顾问：对一只股票出综合建议。

    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        analysis: analyze_trend() 结果
        chip_data: 筹码数据
        intel_data: 情报数据
        stock_info: 基本面数据
        volume_data: 量价数据
        pattern_data: K线形态数据
        top_strategies: 返回前 N 个匹配策略
        openrouter_key: OpenRouter API key
        primary_model: 主 LLM 模型
        fallback_model: 备用模型
        enable_llm: 是否启用 LLM 策略分析（关闭则只返回策略匹配不做分析）

    Returns:
        dict: 顾问建议
    """
    # 如果没传数据，自动拉取
    if analysis is None:
        from ..analysis.trend import analyze_trend
        analysis = analyze_trend(stock_code)

    if chip_data is None:
        try:
            from ..data.fetcher import get_chip_distribution
            chip_data = get_chip_distribution(stock_code)
        except Exception:
            chip_data = {}

    if intel_data is None:
        try:
            from ..data.search import search_comprehensive_intel
            intel_data = search_comprehensive_intel(stock_code, stock_name)
        except Exception:
            intel_data = {}

    if stock_info is None:
        try:
            from ..data.fetcher import get_stock_info
            stock_info = get_stock_info(stock_code)
        except Exception:
            stock_info = {}

    if volume_data is None:
        try:
            from ..analysis.volume import get_volume_analysis
            volume_data = get_volume_analysis(stock_code)
        except Exception:
            volume_data = {}

    if pattern_data is None:
        try:
            from ..analysis.pattern import analyze_pattern
            pattern_data = analyze_pattern(stock_code)
        except Exception:
            pattern_data = {}

    # 1. 铁律检查
    rule_results = check_rules(
        analysis=analysis,
        chip_data=chip_data,
        intel_data=intel_data,
        stock_info=stock_info,
    )
    rules_check = [
        {
            "rule_id": r.rule_id,
            "rule_name": r.rule_name,
            "status": r.status,
            "detail": r.detail,
            "severity": r.severity,
        }
        for r in rule_results
    ]

    # 2. 策略匹配
    strategy_matches = match_strategies(
        analysis=analysis,
        top_n=top_strategies,
    )

    # 3. LLM 策略分析（核心增强）
    strategy_analyses = []
    if enable_llm and strategy_matches:
        from ..llm import analyze_with_strategy

        # 合并所有数据给 LLM
        llm_data = {
            "trend": analysis,
            "volume": volume_data,
            "pattern": pattern_data,
            "intel": intel_data,
        }

        # 只分析匹配度最高的前2个策略（控制成本）
        for strategy in strategy_matches[:2]:
            instructions = strategy.get("instructions", "")
            if not instructions:
                continue

            logger.info("LLM 策略分析: %s → %s", strategy["name"], stock_code)
            llm_opinion = analyze_with_strategy(
                strategy_name=strategy.get("display_name", strategy["name"]),
                strategy_instructions=instructions,
                stock_code=stock_code,
                stock_name=stock_name,
                analysis_data=llm_data,
                api_key=openrouter_key,
            )

            strategy_analyses.append({
                "strategy": strategy.get("display_name", strategy["name"]),
                "strategy_id": strategy["name"],
                "llm_analysis": llm_opinion or "（LLM 分析不可用，策略 instructions 已附在 strategy_matches 中）",
                "match_score": strategy.get("match_score", 0),
            })

    # 4. 风险标记
    risk_flags = intel_data.get("risk_flags", [])
    for r in rule_results:
        if r.status == "fail":
            risk_flags.append({
                "source": f"铁律{r.rule_id}: {r.rule_name}",
                "keyword": r.detail,
            })

    # 5. 综合判断
    fail_count = sum(1 for r in rule_results if r.status == "fail")
    warn_count = sum(1 for r in rule_results if r.status == "warn")
    pass_count = sum(1 for r in rule_results if r.status == "pass")

    signal_score = analysis.get("signal_score", 50) if analysis else 50

    if fail_count >= 2 or (fail_count >= 1 and signal_score < 30):
        overall_status = "danger"
    elif signal_score >= 65 and pass_count >= 4:
        overall_status = "bullish"
    elif signal_score < 35 or fail_count >= 1:
        overall_status = "bearish"
    else:
        overall_status = "neutral"

    # 6. 生成文字意见
    opinion_parts = []

    if fail_count >= 2:
        opinion_parts.append(f"⚠️ {fail_count} 条铁律触发红灯，风险较高，建议谨慎。")
    elif fail_count == 1:
        opinion_parts.append(f"⚠️ 有 1 条铁律未通过，需要关注。")
    elif pass_count >= 5:
        opinion_parts.append("✅ 7 条铁律整体表现良好。")

    if analysis:
        ma_align = analysis.get("ma_alignment", "")
        bias = analysis.get("bias_ma5", 0)
        signal = analysis.get("buy_signal", "")
        score = analysis.get("signal_score", 50)
        opinion_parts.append(
            f"技术面：均线{ma_align}，乖离率 {bias:.1f}%，"
            f"综合评分 {score}/100（{signal}）。"
        )

    # LLM 策略分析摘要
    if strategy_analyses:
        opinion_parts.append("📊 策略分析：")
        for sa in strategy_analyses:
            # 取 LLM 分析的前2句作为摘要
            llm_text = sa["llm_analysis"]
            if llm_text and llm_text != "（LLM 分析不可用，策略 instructions 已附在 strategy_matches 中）":
                first_lines = llm_text.strip().split("\n")[:2]
                opinion_parts.append(f"  【{sa['strategy']}】{' '.join(first_lines)}")

    if risk_flags:
        key_risks = list({r.get("keyword", r.get("source", "")) for r in risk_flags[:3]})
        opinion_parts.append(f"风险提示：{', '.join(key_risks)}。")

    if overall_status == "bullish":
        opinion_parts.append("💡 顾问建议：趋势偏多，可以关注买入机会。")
    elif overall_status == "bearish":
        opinion_parts.append("💡 顾问建议：趋势偏空，建议观望或减仓。")
    elif overall_status == "danger":
        opinion_parts.append("💡 顾问建议：多重风险信号，建议回避。")
    else:
        opinion_parts.append("💡 顾问建议：中性区间，等待更明确的信号。")

    return {
        "rules_check": rules_check,
        "strategy_matches": strategy_matches,
        "strategy_analyses": strategy_analyses,
        "advisor_opinion": "\n".join(opinion_parts),
        "risk_flags": risk_flags,
        "overall_status": overall_status,
    }
