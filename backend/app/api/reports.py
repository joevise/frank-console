# -*- coding: utf-8 -*-
"""报告系统 API — 周报/月报/个股分析，自动填充数据 + DSA生成观点。

模板:
  weekly:  本周市场回顾 + 行业多空变化 + 自选股表现 + 下周展望
  monthly: 月度总结 + 主线回顾 + 持仓分析 + 下月策略
  stock:   个股深度分析(行情/基本面/行业/铁律四维)
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models.models import DailyReport, WatchlistItem, User, Brief
from app.api.market import fetch_quotes_for_codes, _fetch_legacy_analysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["reports"])

DSA_AGENT_URL = "http://dsa-agent:8120/chat"


# ============================================================
# Models
# ============================================================

class ReportRequest(BaseModel):
    report_type: str  # weekly | monthly | stock
    stock_code: Optional[str] = None  # for stock type
    title: Optional[str] = None


# ============================================================
# Helpers
# ============================================================

def _get_watchlist_items(user_id: str, db: Session) -> List[dict]:
    items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user_id,
        WatchlistItem.is_active == True,
    ).all()
    codes = [it.stock_code for it in items]
    quotes = fetch_quotes_for_codes(codes) if codes else {}
    result = []
    for it in items:
        q = quotes.get(it.stock_code, {})
        result.append({
            "code": it.stock_code,
            "name": it.stock_name or q.get("name", it.stock_code),
            "mainline": it.mainline or "",
            "action": it.action or "",
            "price": q.get("price"),
            "change_pct": q.get("change_pct", 0),
        })
    return result


def _get_market_context() -> dict:
    """获取当前市场环境数据。"""
    legacy = _fetch_legacy_analysis()
    bull = legacy.get("当前前10名最长连续多头信号（3,5）的行业", [])
    bear = legacy.get("当前前10名最长连续空头信号（2,4,6）的行业", [])
    new_bull = legacy.get("最新由空头或弱多头转为最强多头的行业", [])
    style = legacy.get("市场风格（风格转换条件：7天内某类行业50%以上转多头，同时其他类行业50%以上转空头）", {})

    return {
        "bull_industries": [{"name": b.get("行业", ""), "days": b.get("持续天数", 0)} for b in bull],
        "bear_industries": [{"name": b.get("行业", ""), "days": b.get("持续天数", 0)} for b in bear],
        "new_bull": [b.get("行业", "") for b in new_bull],
        "style_converting": style.get("是否正在转换", False),
    }


def _call_dsa_for_report(prompt: str, timeout: int = 90) -> str:
    """调用DSA Agent生成报告文本。"""
    full_text = ""
    try:
        resp = requests.post(DSA_AGENT_URL, json={"message": prompt}, stream=True, timeout=timeout)
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8")
            if decoded.startswith("data:"):
                try:
                    data = json.loads(decoded[5:].strip())
                    if data.get("type") == "chunk" and data.get("text"):
                        full_text += data["text"]
                    elif data.get("type") == "done":
                        full_text = data.get("full_text", full_text)
                except Exception:
                    pass
    except Exception as exc:
        logger.warning("DSA report failed: %s", exc)
        return f"（DSA分析暂不可用: {exc}）"
    return full_text.strip()


# ============================================================
# Report Generators
# ============================================================

def _gen_weekly_report(watchlist: List[dict], market: dict) -> dict:
    """生成周报。"""
    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # 市场环境摘要
    bull_text = "、".join([f"{b['name']}({b['days']}天)" for b in market["bull_industries"][:5]])
    bear_text = "、".join([f"{b['name']}({b['days']}天)" for b in market["bear_industries"][:3]])
    new_bull_text = "、".join(market["new_bull"][:3]) if market["new_bull"] else "无"

    # 自选股表现
    holdings_text = "\n".join([
        f"- {h['name']}({h['code']}): 现价{h['price']}，今日{h['change_pct']:+.2f}%，主线: {h['mainline'] or '主线外'}"
        for h in watchlist
    ]) if watchlist else "暂无自选股"

    prompt = f"""请生成一份本周A股市场周报（{week_ago} ~ {today}）。

当前市场数据：
- 多头主线行业: {bull_text}
- 空头行业: {bear_text}
- 新转多头: {new_bull_text}
- 风格转换中: {'是' if market['style_converting'] else '否'}

自选股表现:
{holdings_text}

请按以下结构输出：
## 一、本周市场回顾
（大盘走势、主线变化、关键事件）

## 二、行业多空分析
（多头行业持续性分析、空头行业风险提示、新转多头关注点）

## 三、持仓表现与建议
（逐只点评自选股，给出操作建议）

## 四、下周展望
（重点关注方向、风险提示、操作策略）

每部分2-3段，专业简洁，有观点有数据。"""

    content = _call_dsa_for_report(prompt)

    return {
        "title": f"周报 {today}",
        "report_type": "weekly",
        "date": today,
        "content": content,
        "data_snapshot": {
            "market": market,
            "holdings": watchlist,
        }
    }


def _gen_monthly_report(watchlist: List[dict], market: dict) -> dict:
    """生成月报。"""
    today = datetime.now().strftime("%Y-%m-%d")
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")

    bull_text = "、".join([f"{b['name']}({b['days']}天)" for b in market["bull_industries"][:5]])
    bear_text = "、".join([f"{b['name']}({b['days']}天)" for b in market["bear_industries"][:3]])

    holdings_text = "\n".join([
        f"- {h['name']}({h['code']}): 现价{h['price']}，{h['mainline'] or '主线外'}"
        for h in watchlist
    ]) if watchlist else "暂无自选股"

    prompt = f"""请生成一份{datetime.now().month}月A股市场月报（{month_start} ~ {today}）。

当前市场数据：
- 核心多头主线: {bull_text}
- 主要空头方向: {bear_text}
- 风格转换中: {'是' if market['style_converting'] else '否'}

持仓:
{holdings_text}

请按以下结构输出：
## 一、月度市场总结
（本月行情走势、主线轮动、重大事件影响）

## 二、主线回顾与展望
（本月核心主线表现、持续性分析、下月可能方向）

## 三、持仓月度分析
（逐只分析月度表现、当前状态、调整建议）

## 四、下月策略
（仓位建议、重点方向、风险控制要点）

专业、有数据、有观点，适合给基金经理看。"""

    content = _call_dsa_for_report(prompt)

    return {
        "title": f"月报 {today}",
        "report_type": "monthly",
        "date": today,
        "content": content,
        "data_snapshot": {
            "market": market,
            "holdings": watchlist,
        }
    }


def _gen_stock_report(stock_code: str, watchlist: List[dict], market: dict) -> dict:
    """生成个股深度分析报告。"""
    today = datetime.now().strftime("%Y-%m-%d")

    # 获取个股实时行情
    quotes = fetch_quotes_for_codes([stock_code])
    quote = quotes.get(stock_code, {})

    # 查自选股里有没有这只票
    in_watchlist = next((h for h in watchlist if h["code"] == stock_code), None)

    q_desc = ""
    if quote:
        q_desc = (
            f"现价{quote.get('price')}，今日{quote.get('change_pct',0):+.2f}%，"
            f"最高{quote.get('high')}，最低{quote.get('low')}，"
            f"成交额{quote.get('amount_yi',0):.1f}亿"
        )

    name = quote.get("name") or (in_watchlist or {}).get("name") or stock_code
    mainline = (in_watchlist or {}).get("mainline", "")

    prompt = f"""请对个股 {name}（{stock_code}）生成一份深度分析报告。

当前行情: {q_desc}
所属主线: {mainline or '未标注'}
当前市场多头主线: {"、".join([b["name"] for b in market["bull_industries"][:5]])}

请按以下结构输出：
## 一、基本面概况
（PE/PB/ROE/股息率/市值，估值是否合理）

## 二、技术面分析
（趋势、量价、支撑压力位、布林位置）

## 三、行业定位
（所处行业当前多空状态、是否在主线上、行业排名）

## 四、操作策略
（明确的买入/持有/减仓/止损建议，入场价、止损价、目标价）

## 五、风险提示

专业简洁，数据说话，每部分2-3段。"""

    content = _call_dsa_for_report(prompt)

    return {
        "title": f"{name} 个股分析 {today}",
        "report_type": "stock",
        "date": today,
        "stock_code": stock_code,
        "stock_name": name,
        "content": content,
        "quote": quote,
    }


# ============================================================
# API Routes
# ============================================================

@router.post("/generate")
async def generate_report(
    req: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成报告。type: weekly | monthly | stock"""
    watchlist = _get_watchlist_items(current_user.id, db)
    market = _get_market_context()

    if req.report_type == "weekly":
        report = _gen_weekly_report(watchlist, market)
    elif req.report_type == "monthly":
        report = _gen_monthly_report(watchlist, market)
    elif req.report_type == "stock":
        if not req.stock_code:
            raise HTTPException(400, "stock_code required for stock report")
        report = _gen_stock_report(req.stock_code, watchlist, market)
    else:
        raise HTTPException(400, f"Unknown report type: {req.report_type}")

    # 落库
    db_report = DailyReport(
        user_id=current_user.id,
        report_date=datetime.utcnow(),
        stock_code=req.stock_code or "MARKET",
        stock_name=report.get("title", ""),
        overall_status=req.report_type,
        signal_score=0,
        report_data=report,
    )
    db.add(db_report)
    db.commit()

    report["id"] = db_report.id
    return report


@router.get("/list")
def list_reports(
    report_type: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取报告列表。"""
    q = db.query(DailyReport).filter(DailyReport.user_id == current_user.id)
    if report_type:
        q = q.filter(DailyReport.overall_status == report_type)
    reports = q.order_by(DailyReport.report_date.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "title": (r.report_data or {}).get("title", r.stock_name),
            "report_type": r.overall_status,
            "date": r.report_date.isoformat() if r.report_date else "",
            "stock_code": r.stock_code,
            "preview": ((r.report_data or {}).get("content", "")[:100] + "...") if r.report_data else "",
        }
        for r in reports
    ]


@router.get("/{report_id}")
def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单个报告详情。"""
    r = db.query(DailyReport).filter(
        DailyReport.id == report_id,
        DailyReport.user_id == current_user.id,
    ).first()
    if not r:
        raise HTTPException(404, "Report not found")
    data = r.report_data or {}
    data["id"] = r.id
    return data


@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除报告。"""
    r = db.query(DailyReport).filter(
        DailyReport.id == report_id,
        DailyReport.user_id == current_user.id,
    ).first()
    if not r:
        raise HTTPException(404, "Report not found")
    db.delete(r)
    db.commit()
    return {"ok": True}
