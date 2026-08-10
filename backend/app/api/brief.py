# -*- coding: utf-8 -*-
"""每日晨报 API — 结构化分析师晨报，持久化存储。

晨报结构：
- rating: 评级（attack/caution/defend）
- summary: 三句话结论
- market_data: 大盘数据
- mainlines: 主线跟踪
- risks: 风险信号
- frank_advice: Frank 操作建议
- sources: 所有信息来源链接
- content: 完整 markdown
"""
from __future__ import annotations
import json, logging, os
from datetime import datetime, timedelta
from typing import Any, Dict
import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.auth import get_current_user
from app.core.db import get_db
from app.models.models import User, Brief

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/brief", tags=["brief"])

DSA_AGENT_URL = os.environ.get("DSA_AGENT_URL", "http://dsa-agent:8120")

BRIEF_PROMPT = """请生成今日A股结构化晨报。严格按照以下格式输出：

【评级】（attack=进攻 / caution=震荡 / defend=防守）

【三句话结论】
1. （一句话）
2. （一句话）
3. （一句话）

【大盘数据】
上证指数：xxxx.xx（涨跌幅%）
深证成指：xxxx.xx（涨跌幅%）
创业板指：xxxx.xx（涨跌幅%）
成交额：xxxx亿

【主线跟踪】
1. 板块名（持续X天）— 一句话逻辑
   来源：[新闻标题](URL) 或 [数据源：StockAPI]
2. 板块名（持续X天）— 一句话逻辑
   来源：[新闻标题](URL) 或 [数据源：StockAPI]

【风险信号】
1. 风险描述 — 数据支撑
   来源：[来源](URL)
2. 风险描述 — 数据支撑
   来源：[来源](URL)

【操作建议】
1. 具体建议
2. 具体建议

要求：
- 每个关键观点必须引用数据源或新闻链接
- 先调 news_search 搜索今日重要财经新闻
- 再调 legacy_market_overview 和 legacy_indexes 获取市场数据
- 格式：[来源名称](URL) 或 [数据源：Tushare/StockAPI]
- 没有来源的分析等于没有可信度"""


def _call_dsa_for_brief(timeout: int = 180) -> str:
    """调 DSA Agent 生成晨报（用流式版避免超时）。"""
    from app.services.frank_brain import _call_dsa_with_steps
    full_text = ""
    for event in _call_dsa_with_steps(BRIEF_PROMPT, timeout=timeout):
        if event["type"] == "dsa_done":
            full_text = event.get("full_text", "")
    return full_text


def _parse_brief(content: str) -> Dict[str, Any]:
    """从 DSA 的 markdown 回复中提取结构化字段。"""
    import re

    # 评级
    rating = "caution"
    rating_match = re.search(r'【评级】.*?(attack|caution|defend)', content)
    if rating_match:
        rating = rating_match.group(1)

    # 三句话结论
    summary = ""
    summary_match = re.search(r'【三句话结论】\s*(.*?)(?=【|$)', content, re.DOTALL)
    if summary_match:
        summary = summary_match.group(1).strip()

    # 提取所有链接
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    sources = [{"label": l, "url": u} for l, u in links]

    # 数据源标注
    data_sources = re.findall(r'\[数据源[：:]([^\]]+)\]', content)

    return {
        "rating": rating,
        "summary": summary,
        "sources": sources,
        "data_sources": data_sources,
    }


@router.post("/generate")
def generate_brief(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成今日晨报并落库。"""
    try:
        raw_content = _call_dsa_for_brief()
    except Exception as e:
        logger.exception("晨报生成失败")
        raise HTTPException(status_code=502, detail=f"DSA Agent 调用失败: {str(e)}")

    if not raw_content or len(raw_content) < 50:
        raise HTTPException(status_code=502, detail="晨报内容为空或过短")

    # 解析结构化字段
    parsed = _parse_brief(raw_content)

    # 落库
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    existing = db.query(Brief).filter(
        Brief.user_id == current_user.id,
        Brief.brief_date >= today_start,
    ).first()

    # 把结构化数据存到 data_sources 字段（JSON）
    structured = {
        "rating": parsed["rating"],
        "summary": parsed["summary"],
        "sources": parsed["sources"],
        "data_sources": parsed["data_sources"],
    }

    if existing:
        existing.content = raw_content
        existing.data_sources = structured
        existing.created_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        brief_obj = existing
    else:
        brief_obj = Brief(
            user_id=current_user.id,
            brief_date=datetime.utcnow(),
            content=raw_content,
            data_sources=structured,
        )
        db.add(brief_obj)
        db.commit()
        db.refresh(brief_obj)

    return {
        "id": brief_obj.id,
        "date": brief_obj.brief_date.strftime("%Y-%m-%d"),
        "content": brief_obj.content,
        "rating": parsed["rating"],
        "summary": parsed["summary"],
        "sources": parsed["sources"],
        "data_sources": parsed["data_sources"],
    }


@router.get("/today")
def get_today_brief(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取今日晨报。"""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    brief = db.query(Brief).filter(
        Brief.user_id == current_user.id,
        Brief.brief_date >= today_start,
    ).first()

    if not brief:
        return {"date": datetime.now().strftime("%Y-%m-%d"), "content": "", "rating": "", "summary": "", "sources": []}

    structured = brief.data_sources or {}
    return {
        "id": brief.id,
        "date": brief.brief_date.strftime("%Y-%m-%d"),
        "content": brief.content,
        "rating": structured.get("rating", ""),
        "summary": structured.get("summary", ""),
        "sources": structured.get("sources", []),
        "data_sources": structured.get("data_sources", []),
    }


@router.get("/history")
def get_brief_history(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取最近 N 天的晨报列表（含评级和摘要）。"""
    since = datetime.utcnow() - timedelta(days=days)
    briefs = db.query(Brief).filter(
        Brief.user_id == current_user.id,
        Brief.brief_date >= since,
    ).order_by(Brief.brief_date.desc()).all()

    result = []
    for b in briefs:
        s = b.data_sources or {}
        result.append({
            "id": b.id,
            "date": b.brief_date.strftime("%Y-%m-%d"),
            "rating": s.get("rating", ""),
            "summary": s.get("summary", "")[:80] if s.get("summary") else b.content[:80],
            "preview": b.content[:100] + "..." if len(b.content) > 100 else b.content,
        })
    return result


@router.get("/{brief_id}")
def get_brief_by_id(
    brief_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取指定晨报完整内容。"""
    brief = db.query(Brief).filter(
        Brief.id == brief_id,
        Brief.user_id == current_user.id,
    ).first()
    if not brief:
        raise HTTPException(status_code=404, detail="晨报不存在")

    structured = brief.data_sources or {}
    return {
        "id": brief.id,
        "date": brief.brief_date.strftime("%Y-%m-%d"),
        "content": brief.content,
        "rating": structured.get("rating", ""),
        "summary": structured.get("summary", ""),
        "sources": structured.get("sources", []),
        "data_sources": structured.get("data_sources", []),
    }
