# -*- coding: utf-8 -*-
"""
封装 DSA Legacy API（http://1.94.7.13:5186）的 7 个核心接口。

每个函数返回统一结构：
    {
        "success": bool,
        "tool_name": str,   # 例如 "dsa_market_overview"
        "data": dict,        # 接口原始 payload（已剥外层 success 字段）
        "summary": str,      # 一句话总结，方便 Frank 直接阅读
    }

失败时：
    {
        "success": False,
        "tool_name": str,
        "error": str,
        "summary": str,
    }

环境变量：
    DSA_LEGACY_API_URL  自定义 base_url（默认 http://1.94.7.13:5186）
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

# ============================================================
# 配置
# ============================================================

BASE_URL: str = os.environ.get("DSA_LEGACY_API_URL", "http://1.94.7.13:5186").rstrip("/")
DEFAULT_TIMEOUT: int = 10  # 秒

# 通用请求头：让 API server 看到的是"普通浏览器"
_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Frank-DSA-Researcher/1.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}


# ============================================================
# 底层 HTTP 调用
# ============================================================

def legacy_get(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """统一的 GET 调用封装。

    Args:
        path: 例如 "/api/stock-info"
        params: query 字符串参数（值会被转 str）
        timeout: 超时秒数

    Returns:
        解析后的 JSON dict。HTTP/解析失败抛出异常。
    """
    url = f"{BASE_URL}{path}"
    # 过滤 None 值并把 bool 转成 0/1，匹配 DSA 旧接口习惯
    safe_params: Dict[str, str] = {}
    if params:
        for k, v in params.items():
            if v is None:
                continue
            if isinstance(v, bool):
                safe_params[k] = "1" if v else "0"
            else:
                safe_params[k] = str(v)

    logger.debug("GET %s params=%s", url, safe_params)
    resp = requests.get(
        url,
        params=safe_params,
        headers=_DEFAULT_HEADERS,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def _pack(
    tool_name: str,
    payload: Dict[str, Any],
    summary: str,
) -> Dict[str, Any]:
    """构造统一成功返回。"""
    return {
        "success": True,
        "tool_name": tool_name,
        "data": payload,
        "summary": summary,
    }


def _pack_error(
    tool_name: str,
    error: Exception,
) -> Dict[str, Any]:
    """构造统一失败返回。"""
    return {
        "success": False,
        "tool_name": tool_name,
        "error": f"{type(error).__name__}: {error}",
        "summary": f"{tool_name} 调用失败: {error}",
    }


def _extract_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """剥掉 DSA 接口外层的 {'success': True, 'data': ..., 'message': ...}。"""
    if not isinstance(payload, dict):
        return {"raw": payload}
    if "data" in payload and isinstance(payload["data"], (dict, list)):
        inner = payload["data"]
        if isinstance(inner, dict):
            return inner
        return {"items": inner}
    return payload


# ============================================================
# 1. get_market_overview — 多空分析 + 35 信号行业排名
# ============================================================

def get_market_overview() -> Dict[str, Any]:
    """获取多空分析 + 35 信号行业排名。

    对应接口: GET /api/stock-analysis

    Returns:
        {
            "success": True,
            "tool_name": "dsa_market_overview",
            "data": {
                "当前前10名最长连续多头信号（3,5）的行业": [...],
                "当前前10名最长连续空头信号（2,4,6）的行业": [...],
                "最新由空头或弱多头转为最强多头的行业": [...],
                "最新由多头转为空头的行业": [...],
                "依旧主线行业": [...]
            },
            "summary": "..."
        }
    """
    tool_name = "dsa_market_overview"
    try:
        raw = legacy_get("/api/stock-analysis")
        data = _extract_data(raw)
        # 生成一句话总结
        main_bull = data.get("当前前10名最长连续多头信号（3,5）的行业") or []
        top_industry = main_bull[0]["行业"] if main_bull else "无"
        top_days = main_bull[0]["持续天数"] if main_bull else 0
        n_long = len(main_bull)
        n_short = len(data.get("当前前10名最长连续空头信号（2,4,6）的行业") or [])
        n_flip = len(data.get("最新由空头或弱多头转为最强多头的行业") or [])
        summary = (
            f"主线最强行业 {top_industry}({top_days}天)，"
            f"多头榜{n_long}个，空头榜{n_short}个，今日转强{n_flip}个"
        )
        return _pack(tool_name, data, summary)
    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)


# ============================================================
# 2. get_top_stocks — 打分最高 20 只
# ============================================================

def get_top_stocks() -> Dict[str, Any]:
    """获取打分最高的前 20 只股票。

    对应接口: GET /api/top-20-stocks

    Returns:
        data: list[dict] — 每只含名称/行业/Wind四级行业/当日个股总分/date
    """
    tool_name = "dsa_top_stocks"
    try:
        raw = legacy_get("/api/top-20-stocks")
        items = _extract_data(raw)
        # 旧接口有时候 data 是 list
        if isinstance(items, dict) and "items" in items:
            items = items["items"]
        elif not isinstance(items, list):
            items = items.get("data") if isinstance(items, dict) else []
        n = len(items) if isinstance(items, list) else 0
        if isinstance(items, list) and items:
            top1 = items[0]
            summary = (
                f"Top20共{n}只，第1名 {top1.get('名称','?')}"
                f"({top1.get('行业','?')}) {top1.get('当日个股总分','?')}分"
            )
        else:
            summary = "Top20 数据为空"
        return _pack(tool_name, {"stocks": items}, summary)
    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)


# ============================================================
# 3. get_stock_detail — 个股 140+ 字段详情
# ============================================================

def get_stock_detail(query: str) -> Dict[str, Any]:
    """按代码或简称查个股详情（140+ 字段）。

    对应接口: GET /api/stock-info?query={query}

    Args:
        query: 股票代码（如 "600519"）或名称（如 "贵州茅台"）

    Returns:
        data: list[dict] — 完整字段（boll/pe/pb/roe/机构家数/35 信号等）
    """
    tool_name = "dsa_stock_detail"
    try:
        if not query:
            raise ValueError("query 参数不能为空")
        raw = legacy_get("/api/stock-info", {"query": query})
        data = _extract_data(raw)
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        if not isinstance(data, list):
            data = []
        if data:
            row = data[0]
            summary = (
                f"{row.get('名称', '?')}({row.get('代码', '?')}) "
                f"行业={row.get('行业', '?')} "
                f"涨跌={row.get('涨跌幅', '?')}% "
                f"总分={row.get('当日个股总分_1206_1206', '?')}"
            )
        else:
            summary = f"未查询到 {query} 的详情"
        return _pack(tool_name, {"stocks": data}, summary)
    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)


# ============================================================
# 4. get_hot_industries — 涨停前 5 行业
# ============================================================

def get_hot_industries() -> Dict[str, Any]:
    """获取今日涨停数量前 5 的行业。

    对应接口: GET /api/top-limit-up-industries

    Returns:
        data: {
            "date": str,
            "行业涨停排名": [{"行业": str, "涨停数量": int}, ...]
        }
    """
    tool_name = "dsa_hot_industries"
    try:
        raw = legacy_get("/api/top-limit-up-industries")
        data = _extract_data(raw)
        rank = data.get("行业涨停排名") or data.get("items") or []
        if isinstance(rank, list) and rank:
            top3 = "、".join(
                f"{x.get('行业','?')}({x.get('涨停数量','?')})" for x in rank[:3]
            )
            summary = f"涨停Top3: {top3}"
        else:
            summary = "暂无涨停行业数据"
        return _pack(tool_name, data, summary)
    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)


# ============================================================
# 5. get_industry_limitup — 行业涨停股清单
# ============================================================

def get_industry_limitup(industry: str) -> Dict[str, Any]:
    """按行业名拿涨停股列表（中文自动 URL encode）。

    对应接口: GET /api/industry-limit-up?industry={industry}

    Args:
        industry: 行业中文名，如 "AIGC"、"半导体"

    Returns:
        data: {"行业": str, "涨停数量": int, "涨停股票": [{代码,名称}, ...], "date": str}
    """
    tool_name = "dsa_industry_limitup"
    try:
        if not industry:
            raise ValueError("industry 参数不能为空")
        # 中文 industry 在 URL 中必须 percent-encode（requests 的 params 会自动编码，
        # 但因为我们手动 _pack 字符串参数，这里再显式 quote 一次做兜底）
        encoded = quote(industry, safe="")
        raw = legacy_get(
            "/api/industry-limit-up",
            {"industry": industry, "industry_encoded": encoded},
        )
        data = _extract_data(raw)
        n = data.get("涨停数量", len(data.get("涨停股票") or []))
        summary = f"行业 {industry} 涨停 {n} 只"
        return _pack(tool_name, data, summary)
    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)


# ============================================================
# 6. get_indexes — 三大指数
# ============================================================

def get_indexes() -> Dict[str, Any]:
    """获取上证/深证/创业板三大指数。

    对应接口: GET /api/market-indexes

    Returns:
        data: {
            "sh": {"name": str, "当前指数": float, "日内涨跌幅": float, ...},
            "sz": {...},
            "cyb": {...}
        }
    """
    tool_name = "dsa_indexes"
    try:
        raw = legacy_get("/api/market-indexes")
        data = _extract_data(raw)
        sh = data.get("sh", {})
        sz = data.get("sz", {})
        cyb = data.get("cyb", {})
        summary = (
            f"上证 {sh.get('当前指数', '?')}({sh.get('日内涨跌幅', '?')}%) "
            f"深证 {sz.get('当前指数', '?')}({sz.get('日内涨跌幅', '?')}%) "
            f"创业板 {cyb.get('当前指数', '?')}({cyb.get('日内涨跌幅', '?')}%)"
        )
        return _pack(tool_name, data, summary)
    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)


# ============================================================
# 7. get_history_analysis — 历史某天多空分析（自动 fallback 7 天）
# ============================================================

def _peek_latest_known_date(max_lookback_days: int = 45) -> Optional[datetime]:
    """尝试从 /api/stock-analysis 拿一个最新有数据的日期，作为 fallback 锚点。

    返回 datetime；失败则 None。
    """
    try:
        raw = legacy_get("/api/stock-analysis")
        # data 可能直接是 dict，也可能是 list
        candidates: list = []
        if isinstance(raw, dict):
            inner = raw.get("data", raw)
            if isinstance(inner, dict):
                for key in (
                    "当前前10名最长连续多头信号（3,5）的行业",
                    "依旧主线行业",
                    "最新由空头或弱多头转为最强多头的行业",
                ):
                    arr = inner.get(key) or []
                    if isinstance(arr, list):
                        for item in arr:
                            for date_field in ("结束日期", "当前日期", "日期"):
                                v = item.get(date_field) if isinstance(item, dict) else None
                                if isinstance(v, str) and len(v) >= 10:
                                    candidates.append(v[:10])
        elif isinstance(raw, list):
            candidates = raw
        if not candidates:
            return None
        # 解析，挑最大的
        best: Optional[datetime] = None
        for s in candidates:
            try:
                dt = datetime.strptime(s.replace("/", "-"), "%Y-%m-%d")
            except ValueError:
                continue
            if best is None or dt > best:
                best = dt
        return best
    except Exception as exc:
        logger.debug("peek_latest_known_date failed: %s", exc)
        return None


def get_history_analysis(date: str) -> Dict[str, Any]:
    """取历史某天的 35 信号行业分析。日期往前试最多 7 天。

    对应接口: GET /api/stock-analysis-by-date?date={YYYYMMDD}

    Args:
        date: 任意可解析的日期字符串，支持 "YYYY-MM-DD" / "YYYYMMDD" / "YYYY/MM/DD"

    Returns:
        data: 同 get_market_overview 的 data 结构
        summary: 包含真实命中的日期（可能是向前 fallback 的）
    """
    tool_name = "dsa_history_analysis"
    try:
        # 标准化为 YYYYMMDD
        try:
            dt = datetime.strptime(date.replace("/", "-"), "%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(date, "%Y%m%d")
            except ValueError:
                raise ValueError(f"无法解析日期: {date}")
        date_str = dt.strftime("%Y%m%d")

        # 第一阶段：从用户给的日期往前试 7 天（API 在临近日期常 500）
        last_error: Optional[Exception] = None
        for offset in range(8):
            try_date = (dt - timedelta(days=offset)).strftime("%Y%m%d")
            try:
                raw = legacy_get(
                    "/api/stock-analysis-by-date",
                    {"date": try_date},
                )
                if isinstance(raw, dict) and "error" in raw:
                    raise ValueError(f"API 返回错误: {raw['error']}")
                data = _extract_data(raw)
                if offset == 0:
                    summary = f"{try_date} 多空分析命中"
                else:
                    summary = f"{date_str} 无数据，自动 fallback 到 {try_date}"
                return _pack(tool_name, data, summary)
            except Exception as exc:
                last_error = exc
                logger.debug("date %s failed: %s", try_date, exc)
                continue

        # 第二阶段：尝试从系统最新有数据的日期开始再 fallback（最多 7 天）
        anchor = _peek_latest_known_date()
        if anchor is not None:
            for offset in range(8):
                try_date = (anchor - timedelta(days=offset)).strftime("%Y%m%d")
                try:
                    raw = legacy_get(
                        "/api/stock-analysis-by-date",
                        {"date": try_date},
                    )
                    if isinstance(raw, dict) and "error" in raw:
                        raise ValueError(f"API 返回错误: {raw['error']}")
                    data = _extract_data(raw)
                    summary = (
                        f"{date_str} 无数据，"
                        f"自动 fallback 到系统最近有数据的日期 {try_date}"
                    )
                    return _pack(tool_name, data, summary)
                except Exception as exc:
                    last_error = exc
                    logger.debug("anchor date %s failed: %s", try_date, exc)
                    continue

        raise RuntimeError(
            f"连续多天均无数据 (从 {date_str} 往前), 最后错误: {last_error}"
        )
    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)