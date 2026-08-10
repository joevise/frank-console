# -*- coding: utf-8 -*-
"""
策略加载与路由 — 从 strategies/*.yaml 加载 16 套策略框架，
按市场状态/趋势特征匹配最合适的策略。
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

_STRATEGIES_DIR = os.path.join(os.path.dirname(__file__), "..", "strategies")
_STRATEGIES_DIR = os.path.abspath(_STRATEGIES_DIR)


@lru_cache(maxsize=1)
def _load_all() -> Dict[str, Dict[str, Any]]:
    """加载所有策略 YAML 文件。"""
    result = {}
    if not os.path.isdir(_STRATEGIES_DIR):
        logger.warning("策略目录不存在: %s", _STRATEGIES_DIR)
        return result

    for fname in sorted(os.listdir(_STRATEGIES_DIR)):
        if not fname.endswith(".yaml"):
            continue
        path = os.path.join(_STRATEGIES_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data and "name" in data:
                result[data["name"]] = data
        except Exception as exc:
            logger.warning("加载策略 %s 失败: %s", fname, exc)

    logger.info("已加载 %d 套策略", len(result))
    return result


def list_strategies() -> List[Dict[str, Any]]:
    """列出所有可用策略。"""
    all_strats = _load_all()
    return [
        {
            "name": s["name"],
            "display_name": s.get("display_name", s["name"]),
            "description": s.get("description", ""),
            "category": s.get("category", ""),
            "default_active": s.get("default_active", False),
            "default_priority": s.get("default_priority", 100),
            "market_regimes": s.get("market_regimes", []),
        }
        for s in all_strats.values()
    ]


def get_strategy(skill_id: str) -> Optional[Dict[str, Any]]:
    """获取单个策略详情（含 instructions）。"""
    return _load_all().get(skill_id)


def match_strategies(
    analysis: Optional[Dict[str, Any]] = None,
    market_regime: Optional[str] = None,
    top_n: int = 3,
) -> List[Dict[str, Any]]:
    """按市场状态/趋势特征匹配最合适的策略。

    Args:
        analysis: analyze_trend() 的返回值（用于判断市场状态）
        market_regime: 手动指定市场状态，如 'trending_up', 'volatile', 'sector_hot'
        top_n: 返回前 N 个

    Returns:
        list: [{name, display_name, description, instructions, reason}]
    """
    all_strats = _load_all()
    if not all_strats:
        return []

    # 推断市场状态
    regime = market_regime
    if not regime and analysis:
        alignment = analysis.get("ma_alignment", "")
        trend_strength = analysis.get("trend_strength", 0)
        volume_status = analysis.get("volume_status", "")

        if "多头" in alignment and trend_strength > 3:
            regime = "trending_up"
        elif "空头" in alignment:
            regime = "trending_down"
        elif volume_status == "放量":
            regime = "volatile"
        else:
            regime = "ranging"

    # 按 market_regimes 匹配
    matched = []
    for s in all_strats.values():
        regimes = s.get("market_regimes") or []
        score = 0

        # regime 匹配
        if regime and regime in regimes:
            score += 50

        # 默认激活加分
        if s.get("default_active"):
            score += 10

        # 优先级（越小越优先）
        priority = s.get("default_priority", 100)
        score -= priority * 0.1

        # category 相关性
        category = s.get("category", "")
        if regime == "trending_up" and category in ("trend", "framework"):
            score += 5
        elif regime == "volatile" and category in ("pattern", "reversal"):
            score += 5

        matched.append((score, s))

    # 排序取 top_n
    matched.sort(key=lambda x: -x[0])
    result = []
    for score, s in matched[:top_n]:
        result.append({
            "name": s["name"],
            "display_name": s.get("display_name", s["name"]),
            "description": s.get("description", ""),
            "category": s.get("category", ""),
            "instructions": s.get("instructions", ""),
            "match_score": round(score, 1),
            "reason": f"市场状态={regime or 'unknown'}，策略适配度 {score:.1f}",
        })

    return result
