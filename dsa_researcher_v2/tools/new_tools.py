# -*- coding: utf-8 -*-
"""6 个新增分析工具 — 布林线/基本面/VIX/主线预警/行业偏离度/华尔街观点。

每个函数返回统一格式：
    {"success": bool, "tool_name": str, "data": dict, "summary": str}
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from .market_tools import get_stock_detail, get_market_overview, _pack, _pack_error


def _extract_stock_raw(data: Any) -> Dict[str, Any]:
    """从 get_stock_detail 返回的 data 中提取个股原始 dict。

    market_tools.get_stock_detail 返回 {"stocks": [原始dict]}，
    这里提取 stocks[0] 作为原始数据。
    """
    if isinstance(data, dict) and "stocks" in data:
        stocks = data["stocks"]
        if isinstance(stocks, list) and stocks:
            return stocks[0]
    # fallback：如果结构不匹配，直接返回 data 本身
    return data if isinstance(data, dict) else {}

logger = logging.getLogger(__name__)

_TIMEOUT = 10


# ============================================================
# 1. get_bollinger — 布林线（日线，20日均线±2倍标准差）
# ============================================================

def get_bollinger(stock_code: str) -> Dict[str, Any]:
    """计算布林线通道。

    优先读 get_stock_detail 里的 boll 字段（如果数据源已填充）。
    如果全是 0，fallback 用前60日收盘价自算。

    返回：上轨/中轨/下轨/收盘价/位置百分比/三轨方向/原始数据来源
    """
    tool_name = "dsa_bollinger"
    try:
        detail = get_stock_detail(stock_code)
        if not detail.get("success"):
            raise ValueError(f"get_stock_detail 失败: {detail.get('error')}")

        raw = _extract_stock_raw(detail["data"])
        # 尝试从 API 返回读布林线
        upper = raw.get("boll_upper_qfq", 0)
        mid = raw.get("boll_mid_qfq", 0)
        lower = raw.get("boll_lower_qfq", 0)
        close = raw.get("收盘价", 0)
        position_pct = raw.get("收盘靠近布林线的百分比率", 0)

        if upper and mid and lower:
            # 数据源有布林线值
            data = {
                "stock_code": stock_code,
                "name": raw.get("名称", ""),
                "upper": round(upper, 2),
                "mid": round(mid, 2),
                "lower": round(lower, 2),
                "close": close,
                "position_pct": round(position_pct, 4),
                "source": "api",
            }
        else:
            # fallback：用前60日收盘价自算
            close_prices_str = raw.get("前60交易日收盘价", "[]")
            if isinstance(close_prices_str, str):
                try:
                    prices = json.loads(close_prices_str)
                except Exception:
                    prices = []
            else:
                prices = close_prices_str if isinstance(close_prices_str, list) else []

            if len(prices) < 20:
                raise ValueError(f"收盘价数据不足（仅{len(prices)}条），无法计算布林线")

            prices = [float(p) for p in prices]
            recent_20 = prices[-20:]
            mid_val = sum(recent_20) / 20
            variance = sum((p - mid_val) ** 2 for p in recent_20) / 20
            std = variance ** 0.5
            upper_val = mid_val + 2 * std
            lower_val = mid_val - 2 * std
            close_val = prices[-1]

            pos = (close_val - lower_val) / (upper_val - lower_val) if upper_val != lower_val else 0.5

            data = {
                "stock_code": stock_code,
                "name": raw.get("名称", ""),
                "upper": round(upper_val, 2),
                "mid": round(mid_val, 2),
                "lower": round(lower_val, 2),
                "close": close_val,
                "position_pct": round(pos, 4),
                "source": "calculated_from_60d",
            }

        # 三轨方向判断：用最近5天的中轨（MA20）趋势
        close_prices_str = raw.get("前60交易日收盘价", "[]")
        if isinstance(close_prices_str, str):
            try:
                all_prices = json.loads(close_prices_str)
            except Exception:
                all_prices = []
        else:
            all_prices = close_prices_str if isinstance(close_prices_str, list) else []

        if len(all_prices) >= 25:
            all_prices = [float(p) for p in all_prices]
            ma20_values = []
            for i in range(-5, 0):
                window = all_prices[i - 19:i + 1] if i - 19 >= 0 else all_prices[:i + 1]
                if len(window) >= 20:
                    ma20_values.append(sum(window[-20:]) / 20)

            if len(ma20_values) >= 3:
                diffs = [ma20_values[i] - ma20_values[i - 1] for i in range(1, len(ma20_values))]
                if all(d > 0 for d in diffs):
                    direction = "同向上（趋势上升）"
                elif all(d < 0 for d in diffs):
                    direction = "同向下（趋势下降）"
                else:
                    direction = "不一致（震荡）"
            else:
                direction = "数据不足"
        else:
            direction = "数据不足"

        data["direction"] = direction

        summary = (
            f"布林线({data['source']}): 上轨{data['upper']} 中轨{data['mid']} 下轨{data['lower']} "
            f"位置{data['position_pct']:.1%} {direction}"
        )
        return _pack(tool_name, data, summary)

    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)


# ============================================================
# 2. get_fundamentals — 基本面指标
# ============================================================

def get_fundamentals(stock_code: str) -> Dict[str, Any]:
    """读取个股基本面指标。

    从 get_stock_detail 读取：pe_ttm, pb, dv_ratio(股息率), roe,
    持有它的基金公司家数, 行业估值水平, 行业日涨跌幅, 行业10日累计涨幅
    """
    tool_name = "dsa_fundamentals"
    try:
        detail = get_stock_detail(stock_code)
        if not detail.get("success"):
            raise ValueError(f"get_stock_detail 失败: {detail.get('error')}")

        raw = _extract_stock_raw(detail["data"])

        def _val(key, default=None):
            v = raw.get(key, default)
            if v is None or v == 0 or v == 0.0:
                return None  # 标记为数据未填充
            return v

        data = {
            "stock_code": stock_code,
            "name": raw.get("名称", ""),
            "industry": raw.get("行业", ""),
            "pe_ttm": _val("pe_ttm"),
            "pb": _val("pb"),
            "dv_ratio": _val("dv_ratio"),  # 股息率
            "roe": _val("roe"),
            "total_mv": _val("total_mv"),  # 总市值
            "fund_holders": _val("持有它的基金公司家数"),  # 基金持仓家数
            "industry_valuation": _val("行业估值水平"),  # 行业PE
            "industry_day_chg": _val("行业日涨跌幅"),
            "industry_10d_chg": _val("行业10日累计涨幅"),
        }

        # 标记哪些是缺失的
        missing = [k for k, v in data.items() if v is None and k not in ("stock_code", "name", "industry")]
        data["missing_fields"] = missing

        summary_parts = [f"{data['name']}({stock_code})"]
        if data["pe_ttm"] is not None:
            summary_parts.append(f"PE={data['pe_ttm']}")
        if data["dv_ratio"] is not None:
            summary_parts.append(f"股息率={data['dv_ratio']}%")
        if data["fund_holders"] is not None:
            summary_parts.append(f"基金持仓{data['fund_holders']}家")
        if missing:
            summary_parts.append(f"缺失字段: {','.join(missing[:5])}")

        summary = " ".join(summary_parts)
        return _pack(tool_name, data, summary)

    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)


# ============================================================
# 3. get_vix — VIX 恐慌指数
# ============================================================

def get_vix() -> Dict[str, Any]:
    """获取 VIX 恐慌指数实时值。

    数据源：新浪美股 hq.sinajs.cn 接口
    """
    tool_name = "dsa_vix"
    try:
        # 方案1：Yahoo Finance VIX 页面抓取
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        }
        vix_value = None

        # 尝试从 Google Finance 抓取
        try:
            resp = requests.get(
                "https://www.google.com/finance/quote/VIX:INDEXCBOE",
                headers=headers,
                timeout=_TIMEOUT,
            )
            if resp.ok:
                # 找类似 data-last-price="18.36" 或页面中的数字
                match = re.search(r'data-last-price="([\d.]+)"', resp.text)
                if match:
                    vix_value = float(match.group(1))
        except Exception:
            pass

        # 方案2：从 MarketWatch 抓取
        if vix_value is None:
            try:
                resp = requests.get(
                    "https://www.marketwatch.com/investing/index/vix",
                    headers=headers,
                    timeout=_TIMEOUT,
                )
                if resp.ok:
                    match = re.search(r'class="intraday__price"[^>]*>\s*([\d.]+)', resp.text)
                    if not match:
                        match = re.search(r'VIX[^<]*?<[^>]*>([\d.]+)', resp.text)
                    if match:
                        vix_value = float(match.group(1))
            except Exception:
                pass

        # 方案3：从新浪接口（可能有时返回空）
        if vix_value is None:
            try:
                resp = requests.get(
                    "https://hq.sinajs.cn/list=CBOE_VIX",
                    headers={"Referer": "https://finance.sina.com.cn", **headers},
                    timeout=_TIMEOUT,
                )
                if resp.ok:
                    match = re.search(r'"([^"]+)"', resp.text)
                    if match:
                        parts = match.group(1).split(",")
                        if len(parts) > 1 and parts[1]:
                            vix_value = float(parts[1])
            except Exception:
                pass

        if vix_value is None:
            # 所有方案都失败，返回默认值并标记
            data = {
                "value": None,
                "status": "数据暂不可用",
                "note": "所有VIX数据源均无法访问，请手动查看 https://finance.sina.com.cn/stock/usstock/",
            }
            summary = "VIX: 数据暂不可用（所有数据源均失败）"
            return _pack(tool_name, data, summary)

        if vix_value > 24:
            status = "警惕"
        elif vix_value > 20:
            status = "关注"
        else:
            status = "安全"

        data = {
            "value": vix_value,
            "status": status,
            "thresholds": {"danger": 24, "warning": 20},
        }
        summary = f"VIX: {vix_value}（{status}，>24警惕）"
        return _pack(tool_name, data, summary)

    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)


# ============================================================
# 4. mainline_alert — 新主线预警
# ============================================================

def mainline_alert() -> Dict[str, Any]:
    """检测从空头转多头的行业，触发新主线预警。

    数据源：get_market_overview → '最新由空头或弱多头转为最强多头的行业'
    """
    tool_name = "dsa_mainline_alert"
    try:
        overview = get_market_overview()
        if not overview.get("success"):
            raise ValueError(f"get_market_overview 失败: {overview.get('error')}")

        data = overview["data"]

        # 新转多头的行业
        new_bull = data.get("最新由空头或弱多头转为最强多头的行业", [])
        # 从多头转空头的行业（风险）
        new_bear = data.get("最新由多头转为空头的行业", [])
        # 连续多头最强
        continuous_bull = data.get("当前前10名最长连续多头信号（3,5）的行业", [])

        alert_data = {
            "new_to_bull": [],  # 新转多头（机会）
            "new_to_bear": [],  # 新转空头（风险）
            "top_continuous_bull": [],  # 持续多头前3
            "alert_triggered": False,
        }

        for item in new_bull:
            if isinstance(item, dict):
                alert_data["new_to_bull"].append({
                    "industry": item.get("行业", ""),
                    "prev_signal": item.get("前一日信号", ""),
                    "date": item.get("当前日期", ""),
                })

        for item in new_bear:
            if isinstance(item, dict):
                alert_data["new_to_bear"].append({
                    "industry": item.get("行业", ""),
                    "prev_signal": item.get("前一日信号", ""),
                    "date": item.get("当前日期", ""),
                })

        for item in continuous_bull[:3]:
            if isinstance(item, dict):
                alert_data["top_continuous_bull"].append({
                    "industry": item.get("行业", ""),
                    "days": item.get("持续天数", 0),
                })

        alert_data["alert_triggered"] = len(alert_data["new_to_bull"]) > 0

        summary_parts = []
        if alert_data["new_to_bull"]:
            names = [x["industry"] for x in alert_data["new_to_bull"]]
            summary_parts.append(f"⚠️ 新转多头: {', '.join(names)}")
        if alert_data["new_to_bear"]:
            names = [x["industry"] for x in alert_data["new_to_bear"]]
            summary_parts.append(f"🔻 新转空头: {', '.join(names)}")
        if alert_data["top_continuous_bull"]:
            names = [f"{x['industry']}({x['days']}天)" for x in alert_data["top_continuous_bull"]]
            summary_parts.append(f"持续多头: {', '.join(names)}")

        summary = " | ".join(summary_parts) if summary_parts else "无明显变化"
        return _pack(tool_name, alert_data, summary)

    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)


# ============================================================
# 5. get_industry_deviation — 行业偏离度
# ============================================================

def get_industry_deviation(industry: str) -> Dict[str, Any]:
    """计算行业偏离度（近似）。

    用 get_market_overview 的行业持续天数 + 涨停数据来近似判断行业热度。
    详细偏离度需要行业指数K线数据（暂不可用），这里用可获得的数据做粗判。
    """
    tool_name = "dsa_industry_deviation"
    try:
        overview = get_market_overview()
        if not overview.get("success"):
            raise ValueError(f"get_market_overview 失败")

        data = overview["data"]
        bull_list = data.get("当前前10名最长连续多头信号（3,5）的行业", [])

        # 查找目标行业
        found = None
        for item in bull_list:
            if isinstance(item, dict) and item.get("行业") == industry:
                found = item
                break

        if found:
            days = found.get("持续天数", 0)
            # 持续天数越长，偏离度越大（粗略近似）
            # 10天以内正常，10-20天偏热，20天以上过热
            if days >= 20:
                status = "过热"
                deviation_pct = round(days * 0.5, 1)  # 粗略估计
            elif days >= 10:
                status = "偏热"
                deviation_pct = round(days * 0.3, 1)
            else:
                status = "正常"
                deviation_pct = round(days * 0.2, 1)

            result = {
                "industry": industry,
                "continuous_bull_days": days,
                "estimated_deviation_pct": deviation_pct,
                "status": status,
                "note": "偏离度基于持续天数估算，非精确计算（需行业指数K线数据做精确计算）",
            }
        else:
            # 不在多头榜上
            result = {
                "industry": industry,
                "continuous_bull_days": 0,
                "estimated_deviation_pct": 0,
                "status": "非多头行业",
                "note": "该行业不在当前多头信号前10名中",
            }

        summary = f"{industry}: {result['status']}（多头持续{result['continuous_bull_days']}天，偏离约{result['estimated_deviation_pct']}%）"
        return _pack(tool_name, result, summary)

    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)


# ============================================================
# 6. get_wall_street — 华尔街机构观点
# ============================================================

def get_wall_street() -> Dict[str, Any]:
    """从新浪财经美股频道抓取最新华尔街机构观点标题。"""
    tool_name = "dsa_wall_street"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }
        resp = requests.get(
            "https://finance.sina.com.cn/stock/usstock/",
            headers=headers,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        html = resp.text

        # 提取标题：找包含"华尔街"、"美股"、"机构"、"策略"等关键词的 <a> 标签
        # 简单正则提取 <a ...>标题</a>
        titles = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>([^<]{10,80})</a>', html)

        # 过滤出跟华尔街/机构观点相关的
        keywords = ["华尔街", "美股", "机构", "策略", "高盛", "摩根", "花旗", "美银",
                     "大摩", "小摩", "分析师", "市场", "投资", "经济", "利率", "通胀"]
        filtered = []
        for href, title in titles:
            title = title.strip()
            if any(kw in title for kw in keywords):
                filtered.append({"title": title, "url": href})
            if len(filtered) >= 5:
                break

        if not filtered:
            # 如果关键词过滤太严，取前5条较长的标题
            for href, title in titles[:10]:
                t = title.strip()
                if len(t) >= 15:
                    filtered.append({"title": t, "url": href})
                if len(filtered) >= 5:
                    break

        data = {
            "source": "新浪财经美股频道",
            "items": filtered,
            "fetched_at": datetime.now().isoformat(),
        }
        summary = f"华尔街观点({len(filtered)}条): " + " | ".join(
            x["title"][:30] for x in filtered[:3]
        ) if filtered else "暂无最新华尔街观点"
        return _pack(tool_name, data, summary)

    except Exception as exc:
        logger.warning("%s failed: %s", tool_name, exc)
        return _pack_error(tool_name, exc)
