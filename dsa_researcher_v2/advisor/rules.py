# -*- coding: utf-8 -*-
"""
7 条交易铁律 — DSA 核心交易宪法的独立实现。

每条铁律一个 check 函数，输入技术分析数据，输出 pass/warn/fail。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RuleResult:
    """单条铁律的检查结果。"""
    rule_id: int
    rule_name: str
    status: str       # pass / warn / fail / skip
    detail: str       # 具体说明
    severity: str = "info"  # info / warning / danger


TRADING_RULES = [
    {
        "id": 1,
        "name": "严进策略（不追高）",
        "description": "乖离率 < 2% 最佳买点；2-5% 可小仓；> 5% 严禁追高",
        "key_metric": "bias_ma5",
    },
    {
        "id": 2,
        "name": "趋势交易（顺势而为）",
        "description": "只做 MA5 > MA10 > MA20 多头排列的股票",
        "key_metric": "ma_alignment",
    },
    {
        "id": 3,
        "name": "效率优先（筹码结构）",
        "description": "90%集中度 < 15% 健康；获利比例 70-90% 警惕回吐",
        "key_metric": "chip_distribution",
    },
    {
        "id": 4,
        "name": "买点偏好（回踩支撑）",
        "description": "缩量回踩 MA5 最佳；回踩 MA10 次优；跌破 MA20 观望",
        "key_metric": "support_ma5",
    },
    {
        "id": 5,
        "name": "风险排查（一票否决）",
        "description": "减持/预亏/监管/解禁/行业利空 一票否决",
        "key_metric": "risk_flags",
    },
    {
        "id": 6,
        "name": "估值关注（PE/PB）",
        "description": "PE 明显偏高时在风险点中说明",
        "key_metric": "pe_pb",
    },
    {
        "id": 7,
        "name": "强势趋势股放宽",
        "description": "龙头股/强势趋势可适当放宽乖离率，轻仓追踪设止损",
        "key_metric": "trend_strength",
    },
]


def check_rules(
    analysis: Optional[Dict[str, Any]] = None,
    chip_data: Optional[Dict[str, Any]] = None,
    intel_data: Optional[Dict[str, Any]] = None,
    stock_info: Optional[Dict[str, Any]] = None,
) -> List[RuleResult]:
    """对一只股票逐条检查 7 条铁律。

    Args:
        analysis: analyze_trend() 的返回值
        chip_data: get_chip_distribution() 的返回值
        intel_data: search_comprehensive_intel() 的返回值
        stock_info: get_stock_info() 的返回值（含 PE/PB）

    Returns:
        List[RuleResult]: 7 条铁律的检查结果
    """
    results: List[RuleResult] = []
    analysis = analysis or {}
    chip_data = chip_data or {}
    intel_data = intel_data or {}
    stock_info = stock_info or {}

    # ---- 铁律 1：不追高 ----
    bias = analysis.get("bias_ma5")
    if bias is None:
        results.append(RuleResult(1, "严进策略（不追高）", "skip", "无乖离率数据"))
    elif abs(bias) < 2:
        results.append(RuleResult(1, "严进策略（不追高）", "pass",
                                  f"乖离率 {bias:.1f}%，最佳买点区间", "info"))
    elif abs(bias) < 5:
        results.append(RuleResult(1, "严进策略（不追高）", "warn",
                                  f"乖离率 {bias:.1f}%，可小仓介入", "warning"))
    else:
        results.append(RuleResult(1, "严进策略（不追高）", "fail",
                                  f"乖离率 {bias:.1f}% > 5%，严禁追高！", "danger"))

    # ---- 铁律 2：多头排列 ----
    alignment = analysis.get("ma_alignment", "")
    if "多头" in alignment:
        results.append(RuleResult(2, "趋势交易（顺势而为）", "pass",
                                  "MA5 > MA10 > MA20 多头排列", "info"))
    elif "空头" in alignment:
        results.append(RuleResult(2, "趋势交易（顺势而为）", "fail",
                                  "空头排列，坚决不碰", "danger"))
    else:
        results.append(RuleResult(2, "趋势交易（顺势而为）", "warn",
                                  f"均线{alignment}，方向不明", "warning"))

    # ---- 铁律 3：筹码结构 ----
    if chip_data and chip_data.get("concentration"):
        conc = chip_data["concentration"]
        profit_ratio = chip_data.get("profit_ratio", 0)
        if conc < 15 and profit_ratio < 70:
            results.append(RuleResult(3, "效率优先（筹码结构）", "pass",
                                      f"集中度 {conc:.1f}%，获利盘 {profit_ratio:.0f}%，结构健康", "info"))
        elif profit_ratio > 90:
            results.append(RuleResult(3, "效率优先（筹码结构）", "warn",
                                      f"获利盘 {profit_ratio:.0f}% > 90%，警惕回吐", "warning"))
        else:
            results.append(RuleResult(3, "效率优先（筹码结构）", "warn",
                                      f"集中度 {conc:.1f}%，获利盘 {profit_ratio:.0f}%", "warning"))
    else:
        results.append(RuleResult(3, "效率优先（筹码结构）", "skip", "无筹码数据"))

    # ---- 铁律 4：回踩支撑 ----
    support_ma5 = analysis.get("support_ma5")
    volume_status = analysis.get("volume_status", "")
    if support_ma5 is True and "缩量" in volume_status:
        results.append(RuleResult(4, "买点偏好（回踩支撑）", "pass",
                                  "缩量回踩 MA5，最佳买点", "info"))
    elif support_ma5 is True:
        results.append(RuleResult(4, "买点偏好（回踩支撑）", "pass",
                                  "价格在 MA5 上方", "info"))
    elif analysis.get("support_ma10") is True:
        results.append(RuleResult(4, "买点偏好（回踩支撑）", "warn",
                                  "跌破 MA5 但在 MA10 上方，次优买点", "warning"))
    else:
        results.append(RuleResult(4, "买点偏好（回踩支撑）", "fail",
                                  "跌破 MA20，观望", "danger"))

    # ---- 铁律 5：风险排查 ----
    risk_flags = intel_data.get("risk_flags", [])
    if risk_flags:
        keywords = [r.get("keyword", "") for r in risk_flags[:5]]
        results.append(RuleResult(5, "风险排查（一票否决）", "fail",
                                  f"发现风险信号：{', '.join(keywords)}", "danger"))
    else:
        results.append(RuleResult(5, "风险排查（一票否决）", "pass",
                                  "未发现明显利空消息", "info"))

    # ---- 铁律 6：估值 ----
    pe = stock_info.get("pe") or stock_info.get("pe_ttm")
    if pe is not None:
        if pe < 0:
            results.append(RuleResult(6, "估值关注（PE/PB）", "warn",
                                      f"PE={pe:.1f}（亏损）", "warning"))
        elif pe > 80:
            results.append(RuleResult(6, "估值关注（PE/PB）", "warn",
                                      f"PE={pe:.1f} 明显偏高", "warning"))
        elif pe > 40:
            results.append(RuleResult(6, "估值关注（PE/PB）", "pass",
                                      f"PE={pe:.1f} 偏高但可接受", "info"))
        else:
            results.append(RuleResult(6, "估值关注（PE/PB）", "pass",
                                      f"PE={pe:.1f} 合理", "info"))
    else:
        results.append(RuleResult(6, "估值关注（PE/PB）", "skip", "无 PE 数据"))

    # ---- 铁律 7：强势股放宽 ----
    trend_strength = analysis.get("trend_strength", 0)
    signal_score = analysis.get("signal_score", 50)
    if trend_strength > 5 and signal_score > 65:
        results.append(RuleResult(7, "强势趋势股放宽", "pass",
                                  f"趋势强度 {trend_strength:.1f}%，可适当放宽乖离率，轻仓追踪设止损", "info"))
    else:
        results.append(RuleResult(7, "强势趋势股放宽", "skip",
                                  f"趋势强度 {trend_strength:.1f}%，不适用放宽条件"))

    return results
