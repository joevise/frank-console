# -*- coding: utf-8 -*-
"""个股诊断 API — 四维全真实评分。

技术面: 新浪实时行情算
基本面: Tushare daily_basic (PE/PB/ROE/股息率) → 评分
行业面: stockai-api 多头主线匹配 + 行业排名
铁律:   规则引擎 (趋势/量价/位置/纪律四项)
DSA观点: DSA Agent 生成一句话诊断
"""
from __future__ import annotations
import json
import logging
from typing import Any, Dict, Optional

import requests
from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.api.market import fetch_quotes_for_codes, get_bull_industry_names, _fetch_legacy_analysis
from app.services.frank_brain import _call_dsa_stream
from app.models.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analyze", tags=["analyze"])

DSA_AGENT_URL = "http://dsa-agent:8120/chat"
TUSHARE_URL = "https://api.tushare.pro"
TUSHARE_TOKEN = "1f2efbb5be1015f9ee92da4513e9fe5eea847f9722b9a06cbaf80b26"

# 简单内存缓存（避免频繁调 Tushare）
_fundamental_cache: Dict[str, dict] = {}


def _tech_score(quote: Dict[str, Any]) -> int:
    """技术面评分 0-100，基于实时行情。"""
    if not quote:
        return 0
    change_pct = quote.get("change_pct", 0) or 0
    high = quote.get("high", 0) or 0
    low = quote.get("low", 0) or 0
    price = quote.get("price", 0) or 0
    score = 50 + max(-25, min(25, change_pct * 5))
    if high > low:
        pos = (price - low) / (high - low)
        score += (pos - 0.5) * 30
    return max(0, min(100, round(score)))


def _tushare_code(code: str) -> str:
    """转换股票代码为 Tushare 格式。"""
    code = code.strip().upper()
    if "." in code:
        return code
    if code.startswith("6"):
        return f"{code}.SH"
    if code.startswith(("0", "3")):
        return f"{code}.SZ"
    if code.startswith(("4", "8")):
        return f"{code}.BJ"
    return f"{code}.SH"


def _fetch_fundamental(code: str) -> Optional[dict]:
    """从 Tushare 获取基本面数据（带缓存）。"""
    if code in _fundamental_cache:
        cached = _fundamental_cache[code]
        # 缓存1小时内有效
        import time
        if time.time() - cached.get("_ts", 0) < 3600:
            return cached

    ts_code = _tushare_code(code)
    try:
        r = requests.post(TUSHARE_URL, json={
            "api_name": "daily_basic",
            "token": TUSHARE_TOKEN,
            "params": {"ts_code": ts_code},
            "fields": "ts_code,trade_date,pe,pb,ps,total_mv,circ_mv,dv_ratio"
        }, timeout=8)
        data = r.json()
        if data.get("code") == 0 and data.get("data", {}).get("items"):
            item = data["data"]["items"][0]
            item["_ts"] = __import__("time").time()
            _fundamental_cache[code] = item
            return item
    except Exception as e:
        logger.warning("Tushare fundamental failed for %s: %s", code, e)
    return None


def _fundamental_score(fund: Optional[dict]) -> tuple:
    """基本面评分 0-100，基于PE/PB/股息率。
    返回 (score, factors_dict)
    """
    if not fund:
        return 50, {"note": "数据暂不可用"}

    pe = fund.get("pe")
    pb = fund.get("pb")
    dv = fund.get("dv_ratio")

    factors = {}
    score = 50

    # PE评分：合理区间15-30加分
    if pe and pe > 0:
        factors["pe"] = round(pe, 1)
        if pe < 15:
            score += 15  # 低估
        elif pe < 30:
            score += 10  # 合理
        elif pe < 60:
            score -= 5   # 偏高
        else:
            score -= 15   # 高估

    # PB评分：1-5合理
    if pb and pb > 0:
        factors["pb"] = round(pb, 2)
        if pb < 1:
            score += 10  # 破净
        elif pb < 3:
            score += 5   # 合理
        elif pb > 8:
            score -= 10   # 高估

    # 股息率：越高越好
    if dv and dv > 0:
        factors["dv_ratio"] = round(dv, 2)
        if dv > 3:
            score += 10  # 高股息
        elif dv > 1:
            score += 5

    factors["total_mv_yi"] = round(fund.get("total_mv", 0) / 10000, 1) if fund.get("total_mv") else None

    return max(0, min(100, round(score))), factors


def _industry_score(code: str, stock_name: str) -> tuple:
    """行业面评分：是否在多头主线 + 行业整体强弱。
    返回 (score, industry_name)
    """
    bull_names = get_bull_industry_names()
    legacy = _fetch_legacy_analysis()

    # 尝试匹配行业
    industry_name = ""

    # 从 stockai-api 查个股的行业（如果有）
    # 也可以从自选股的 mainline 字段判断
    bull = legacy.get("当前前10名最长连续多头信号（3,5）的行业", [])

    # 简单匹配：如果股票名包含某个多头行业关键词
    for b in bull:
        ind = b.get("行业", "")
        if ind and stock_name and ind in stock_name:
            industry_name = ind
            return 80 + min(15, (b.get("持续天数", 0))), industry_name

    # 默认评分
    if bull_names:
        return 55, "主线外"
    return 45, "主线外"


def _rules_score(quote: Optional[dict], tech: int, fund_score: int, industry: int) -> tuple:
    """铁律评分 — Frank的交易纪律规则引擎。

    四项规则：
    1. 趋势确认：当日涨跌幅方向
    2. 量价配合：成交额是否充足（简化：有数据=合格）
    3. 位置安全：价格在日内区间位置
    4. 纪律执行：综合评分是否达到操作标准

    返回 (score, violations_list)
    """
    score = 50
    violations = []

    if not quote:
        return 50, ["行情数据缺失"]

    change_pct = quote.get("change_pct", 0) or 0
    high = quote.get("high", 0) or 0
    low = quote.get("low", 0) or 0
    price = quote.get("price", 0) or 0
    amount_yi = quote.get("amount_yi", 0) or 0

    # 规则1: 趋势确认 — 跌幅超-3%扣分
    if change_pct < -3:
        score -= 20
        violations.append("跌幅过大(>-3%)，趋势破坏")
    elif change_pct < -1:
        score -= 10
        violations.append("下跌趋势中")
    elif change_pct > 3:
        score += 15
    elif change_pct > 0:
        score += 8

    # 规则2: 量价配合 — 成交额太小扣分
    if amount_yi < 1:
        score -= 10
        violations.append("成交额不足，流动性差")
    elif amount_yi > 10:
        score += 10

    # 规则3: 位置安全 — 接近日内最高加分
    if high > low and high > 0:
        pos = (price - low) / (high - low)
        if pos > 0.8:
            score += 10
        elif pos < 0.2:
            score -= 10
            violations.append("接近日内低点")

    # 规则4: 综合纪律 — 技术面+基本面低于阈值警告
    if tech < 30:
        score -= 15
        violations.append("技术面过弱")
    if fund_score < 30:
        score -= 10
        violations.append("基本面过弱")

    # 多头主线加分
    if industry >= 70:
        score += 10
    elif industry < 40:
        score -= 10
        violations.append("不在多头主线")

    return max(0, min(100, round(score))), violations


def _call_dsa_opinion(code: str, name: str, quote: Dict[str, Any], mainline: str,
                      radar: dict, violations: list) -> Dict[str, Any]:
    """调 DSA Agent 生成个股观点，同时返回工具调用步骤。"""
    q_desc = ""
    if quote:
        q_desc = (
            f"现价{quote.get('price')}，涨跌{quote.get('change_pct')}%，"
            f"最高{quote.get('high')}，最低{quote.get('low')}，"
            f"成交额{quote.get('amount_yi')}亿"
        )
    violation_str = "；".join(violations) if violations else "无违规"
    msg = (
        f"请对个股 {name}（{code}）做一个简短诊断。"
        f"当前行情：{q_desc}。所属主线：{mainline or '未标注'}。"
        f"四维评分：技术{radar['tech']}、基本面{radar['fundamental']}、"
        f"行业{radar['industry']}、铁律{radar['rules']}。"
        f"铁律违规：{violation_str}。"
        f"请给出：1) 一句话核心观点 2) 明确的操作建议（加仓/持有/减仓/止损/观察）。"
        f"控制在150字内，直接给结论。"
    )

    # 用流式版获取工具调用过程
    steps = []
    full_text = ""
    for event in _call_dsa_stream(msg, timeout=90):
        if event["type"] == "dsa_step":
            steps.append(event["text"])
        elif event["type"] == "dsa_done":
            full_text = event.get("full_text", "")

    if not full_text:
        return {"summary": "DSA 分析暂不可用", "action": "", "steps": steps}

    action = ""
    for kw in ["止损", "减仓", "加仓", "持有", "观察"]:
        if kw in full_text:
            action = kw
            break
    return {"summary": full_text.strip(), "action": action, "steps": steps}


@router.get("/stock/{code}")
async def analyze_stock(
    code: str,
    current_user: User = Depends(get_current_user),
):
    """个股四维诊断：技术面 + 基本面 + 行业面 + 铁律，全真实数据。"""
    # 1. 实时行情
    quotes = fetch_quotes_for_codes([code])
    quote = quotes.get(code)
    name = quote.get("name") if quote else code

    # 2. 技术面
    tech = _tech_score(quote)

    # 3. 基本面（Tushare PE/PB/ROE）
    fund_data = _fetch_fundamental(code)
    fund_score, fund_factors = _fundamental_score(fund_data)

    # 4. 行业面
    industry_score_val, industry_name = _industry_score(code, name)

    # 5. 铁律
    rules_score_val, violations = _rules_score(quote, tech, fund_score, industry_score_val)

    radar = {
        "tech": tech,
        "fundamental": fund_score,
        "industry": industry_score_val,
        "rules": rules_score_val,
    }

    # 6. DSA观点
    dsa = _call_dsa_opinion(code, name, quote, industry_name, radar, violations)

    return {
        "stock_code": code,
        "stock_name": name,
        "quote": quote,
        "radar": radar,
        "fundamental_factors": fund_factors,
        "industry_name": industry_name,
        "rule_violations": violations,
        "dsa_steps": dsa.get("steps", []),
        "summary": dsa["summary"],
        "action": dsa["action"],
    }


from fastapi.responses import StreamingResponse

@router.get("/stock/{code}/stream")
async def analyze_stock_stream(
    code: str,
    current_user: User = Depends(get_current_user),
):
    """个股诊断 SSE 流式版 — 实时推送步骤+结果。"""

    def generate():
        # 1. 行情
        yield _sse({"type": "step", "text": "获取实时行情数据…"})
        quotes = fetch_quotes_for_codes([code])
        quote = quotes.get(code)
        name = quote.get("name") if quote else code

        yield _sse({"type": "step", "text": "计算技术面评分…"})
        tech = _tech_score(quote)

        # 2. 基本面
        yield _sse({"type": "step", "text": "查询基本面(PE/PB/ROE)…"})
        fund_data = _fetch_fundamental(code)
        fund_score, fund_factors = _fundamental_score(fund_data)

        # 3. 行业面
        yield _sse({"type": "step", "text": "匹配行业多空主线…"})
        industry_score_val, industry_name = _industry_score(code, name)

        # 4. 铁律
        yield _sse({"type": "step", "text": "执行铁律规则引擎…"})
        rules_score_val, violations = _rules_score(quote, tech, fund_score, industry_score_val)

        radar = {
            "tech": tech, "fundamental": fund_score,
            "industry": industry_score_val, "rules": rules_score_val,
        }

        # 5. 推送四维评分（前端可以先渲染雷达图）
        yield _sse({"type": "radar", "radar": radar, "quote": quote, "stock_name": name,
                     "fundamental_factors": fund_factors, "industry_name": industry_name,
                     "rule_violations": violations})

        # 6. DSA 诊断（实时推送每个工具调用）
        yield _sse({"type": "step", "text": "DSA 分析师诊断中…"})
        dsa = _call_dsa_opinion(code, name, quote, industry_name, radar, violations)

        # 推送 DSA 步骤
        for step in dsa.get("steps", []):
            yield _sse({"type": "dsa_step", "text": step})

        # 最终结果
        yield _sse({"type": "done", "summary": dsa["summary"], "action": dsa["action"],
                     "dsa_steps": dsa.get("steps", [])})

    return StreamingResponse(generate(), media_type="text/event-stream")


def _sse(data: dict) -> str:
    """格式化为 SSE。"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
