# -*- coding: utf-8 -*-
"""Market API — real-time data from Sina Finance + 1.94 stock-analysis API.

Data sources:
- Sina hq.sinajs.cn: real-time index/stock quotes (free, no key)
- 1.94.7.13:5186: industry bull/bear analysis (multi-air signals)
"""
from __future__ import annotations
import logging, re
from datetime import datetime
from typing import Any, Dict, List
import requests
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/market", tags=["market"])

SINA_HEADERS = {"Referer": "https://finance.sina.com.cn"}
LEGACY_API = "https://stockai-api.futurx.cc"

# Index codes for Sina
INDEX_CODES = {
    "sh": ("sh000001", "上证指数"),
    "sz": ("sz399001", "深证成指"),
    "cyb": ("sz399006", "创业板指"),
    "kc50": ("sh000688", "科创50"),
}


def _parse_sina_quote(raw: str) -> Dict[str, Any] | None:
    """Parse one sina hq_str line."""
    m = re.search(r'hq_str_\w+="([^"]*)"', raw)
    if not m:
        return None
    parts = m.group(1).split(",")
    if len(parts) < 32:
        return None
    name = parts[0].strip()
    open_p = float(parts[1]) if parts[1] else 0
    prev_close = float(parts[2]) if parts[2] else 0
    current = float(parts[3]) if parts[3] else 0
    high = float(parts[4]) if parts[4] else 0
    low = float(parts[5]) if parts[5] else 0
    volume = float(parts[8]) if parts[8] else 0  # shares
    amount = float(parts[9]) if parts[9] else 0  # yuan
    date = parts[30] if len(parts) > 30 else ""
    time = parts[31] if len(parts) > 31 else ""

    change = current - prev_close
    change_pct = round(change / prev_close * 100, 2) if prev_close else 0

    return {
        "name": name,
        "price": current,
        "open": open_p,
        "prev_close": prev_close,
        "high": high,
        "low": low,
        "change": round(change, 2),
        "change_pct": change_pct,
        "volume": volume,
        "amount": amount,
        "amount_yi": round(amount / 1e8, 2),  # convert to 亿
        "date": date,
        "time": time,
    }


def _fetch_sina_quotes(codes: List[str]) -> Dict[str, Any]:
    """Fetch real-time quotes from Sina."""
    url = f"https://hq.sinajs.cn/list={','.join(codes)}"
    try:
        resp = requests.get(url, headers=SINA_HEADERS, timeout=5)
        resp.encoding = "gbk"
        result = {}
        for i, line in enumerate(resp.text.strip().split("\n")):
            parsed = _parse_sina_quote(line)
            if parsed:
                result[codes[i]] = parsed
        return result
    except Exception as e:
        logger.warning("Sina fetch failed: %s", e)
        return {}


def _fetch_legacy_analysis() -> Dict[str, Any]:
    """Fetch industry bull/bear analysis from 1.94 API."""
    try:
        resp = requests.get(f"{LEGACY_API}/api/stock-analysis", timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("Legacy API failed: %s", e)
        return {}


def _rating_from_data(bull_industries: list, bear_industries: list, style_data: dict) -> str:
    """Determine market rating from data."""
    if not bull_industries:
        return "caution"
    top_bull_days = bull_industries[0].get("持续天数", 0) if bull_industries else 0
    top_bear_days = bear_industries[0].get("持续天数", 0) if bear_industries else 0

    if top_bull_days >= 10 and top_bear_days < 10:
        return "attack"
    elif top_bear_days >= 15:
        return "defend"
    else:
        return "caution"


def _market_status() -> str:
    """Determine if market is trading based on Beijing time (weekday 9:30-11:30, 13:00-15:00)."""
    from datetime import datetime, timezone, timedelta
    beijing = timezone(timedelta(hours=8))
    now = datetime.now(beijing)
    # Weekend
    if now.weekday() >= 5:
        return "closed"
    t = now.hour * 100 + now.minute
    if (930 <= t <= 1130) or (1300 <= t <= 1500):
        return "trading"
    return "closed"


# ============================================================
# API Routes
# ============================================================

@router.get("/overview")
async def get_market_overview():
    """Real-time market indexes from Sina."""
    codes = [v[0] for v in INDEX_CODES.values()]
    raw = _fetch_sina_quotes(codes)

    indexes = {}
    for key, (code, name) in INDEX_CODES.items():
        if code in raw:
            d = raw[code]
            indexes[key] = d
        else:
            indexes[key] = {"name": name, "price": 0, "change_pct": 0}

    # total turnover (sum of sh+sz amount in 亿)
    total_amount = 0
    for k in ("sh", "sz"):
        if k in indexes and indexes[k].get("amount_yi"):
            total_amount += indexes[k]["amount_yi"]

    # Determine status from legacy data (non-blocking, default to caution if fails)
    try:
        legacy = _fetch_legacy_analysis()
        bull = legacy.get("当前前10名最长连续多头信号（3,5）的行业", [])
        bear = legacy.get("当前前10名最长连续空头信号（2,4,6）的行业", [])
        status = _rating_from_data(bull, bear, legacy.get("市场风格", {}))
    except:
        status = "caution"

    return {
        "indexes": indexes,
        "turnover_yi": round(total_amount, 2),
        "rating": status,
        "status": _market_status(),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/mainlines")
async def get_mainlines():
    """Industry bull/bear rankings from 1.94 API."""
    legacy = _fetch_legacy_analysis()
    if not legacy:
        return {"bull": [], "bear": [], "new_bull": [], "style": None}

    bull = legacy.get("当前前10名最长连续多头信号（3,5）的行业", [])
    bear = legacy.get("当前前10名最长连续空头信号（2,4,6）的行业", [])
    new_bull = legacy.get("最新由空头或弱多头转为最强多头的行业", [])
    new_bear = legacy.get("最新由多头转为空头的行业", [])
    mainline = legacy.get("依旧主线行业", [])
    style = legacy.get("市场风格（风格转换条件：7天内某类行业50%以上转多头，同时其他类行业50%以上转空头）", {})
    strongest = legacy.get("多头信号最强行业类型", [])

    return {
        "bull": bull[:8],
        "bear": bear[:8],
        "new_bull": new_bull[:8],
        "new_bear": new_bear,
        "mainline": mainline,
        "style": style,
        "strongest_type": strongest[0] if strongest else None,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/signals")
async def get_signals():
    """Trading signals with full detail from 1.94 analysis."""
    legacy = _fetch_legacy_analysis()
    if not legacy:
        return {"buy": [], "sell": [], "watch": []}

    new_bull = legacy.get("最新由空头或弱多头转为最强多头的行业", [])
    new_bear = legacy.get("最新由多头转为空头的行业", [])
    bear = legacy.get("当前前10名最长连续空头信号（2,4,6）的行业", [])
    bull = legacy.get("当前前10名最长连续多头信号（3,5）的行业", [])

    # Build lookup from bull/bear for detail
    bull_map = {item.get("行业", ""): item for item in bull}
    bear_map = {item.get("行业", ""): item for item in bear}

    buy_signals = []
    for item in new_bull[:5]:
        name = item.get("行业", "")
        bull_info = bull_map.get(name, {})
        buy_signals.append({
            "stock": name,
            "reason": "新转多头",
            "detail": {
                "signal": item.get("当前日期", ""),
                "prev_signal": item.get("前一日信号", ""),
                "trend_days": bull_info.get("持续天数", 0),
                "start_date": bull_info.get("开始日期", ""),
            }
        })

    sell_signals = []
    for item in bear[:5]:
        name = item.get("行业", "")
        sell_signals.append({
            "stock": name,
            "reason": f"空头持续{item.get('持续天数', '?')}天",
            "detail": {
                "trend_days": item.get("持续天数", 0),
                "start_date": item.get("开始日期", ""),
                "end_date": item.get("结束日期", ""),
            }
        })
    for item in new_bear[:3]:
        name = item.get("行业", "")
        sell_signals.append({
            "stock": name,
            "reason": "由多头转空",
            "detail": {
                "signal": item.get("当前日期", ""),
                "prev_signal": item.get("前一日信号", ""),
            }
        })

    watch_signals = []
    style = legacy.get("市场风格（风格转换条件：7天内某类行业50%以上转多头，同时其他类行业50%以上转空头）", {})
    if style and style.get("是否正在转换"):
        for detail in style.get("转换详情", [])[:4]:
            watch_signals.append({
                "stock": detail.get("转强类别", ""),
                "reason": f"风格转换中，{detail.get('转强比例', '')}转强",
                "detail": {
                    "strong_count": detail.get("转强行业数", 0),
                    "total_count": detail.get("总行业数", 0),
                    "ratio": detail.get("转强比例", ""),
                    "industries": detail.get("转强行业", [])[:5],
                }
            })

    return {"buy": buy_signals, "sell": sell_signals, "watch": watch_signals}


@router.get("/quote/{code}")
async def get_stock_quote(code: str):
    """Real-time quote for a single stock/index."""
    sina_code = to_sina_code(code)
    raw = _fetch_sina_quotes([sina_code])
    if sina_code in raw:
        return raw[sina_code]
    return {"error": "quote not found"}


# ============================================================
# Shared helpers (used by watchlist.py for health scoring)
# ============================================================

def to_sina_code(code: str) -> str:
    """Convert a bare stock code (e.g. 600519 / 300115) to sina format (sh600519 / sz300115)."""
    code = code.strip().lower()
    if code.startswith(("sh", "sz", "bj")):
        return code
    if code.startswith("6"):
        return f"sh{code}"
    if code.startswith(("0", "3")):
        return f"sz{code}"
    if code.startswith(("4", "8")):
        return f"bj{code}"
    return f"sh{code}"


def fetch_quotes_for_codes(codes: List[str]) -> Dict[str, Any]:
    """Fetch real-time quotes for a list of bare stock codes. Returns {bare_code: quote}."""
    if not codes:
        return {}
    sina_codes = [to_sina_code(c) for c in codes]
    raw = _fetch_sina_quotes(sina_codes)
    result = {}
    for bare, sina in zip(codes, sina_codes):
        if sina in raw:
            result[bare] = raw[sina]
    return result


def compute_health(quote: Dict[str, Any], in_mainline: bool) -> Dict[str, Any]:
    """Compute a 0-100 health score from real-time quote + mainline membership.

    Factors:
    - Trend/momentum from change_pct (day performance)
    - Position within day range (price vs high/low)
    - Bonus if stock's industry is a bull mainline
    """
    if not quote:
        return {"score": None, "status": "unknown", "factors": {}}

    change_pct = quote.get("change_pct", 0) or 0
    high = quote.get("high", 0) or 0
    low = quote.get("low", 0) or 0
    price = quote.get("price", 0) or 0

    # Base 50, momentum contributes +-30
    momentum = max(-30, min(30, change_pct * 6))

    # Position in day range contributes 0-15
    if high > low:
        pos_ratio = (price - low) / (high - low)
        position = pos_ratio * 15
    else:
        position = 7.5

    # Mainline bonus
    mainline_bonus = 10 if in_mainline else 0

    score = round(50 + momentum + position + mainline_bonus)
    score = max(0, min(100, score))

    if score >= 70:
        status = "healthy"
    elif score >= 45:
        status = "neutral"
    else:
        status = "weak"

    return {
        "score": score,
        "status": status,
        "factors": {
            "change_pct": change_pct,
            "momentum": round(momentum, 1),
            "position": round(position, 1),
            "in_mainline": in_mainline,
        },
    }


def get_bull_industry_names() -> set:
    """Return set of current bull mainline industry names."""
    legacy = _fetch_legacy_analysis()
    if not legacy:
        return set()
    bull = legacy.get("当前前10名最长连续多头信号（3,5）的行业", [])
    return {item.get("行业", "") for item in bull}
