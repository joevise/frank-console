"""DSA Agent FastAPI 服务 — Frank 的专属分析师顾问。

核心接口：
- POST /chat — 自由对话（DSA 的主要入口）
- POST /analyze — 个股深度诊断
- POST /market_brief — 当日市场报告
- GET /health — 健康检查
"""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict, Generator, List, Optional

import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..core.config import get_settings
from ..data import tushare_client as ts
from ..data import legacy_client as legacy
from ..search import news_search as news

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger("dsa_agent")

app = FastAPI(title="DSA Agent API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ============================================================
# DSA 分析师 System Prompt
# ============================================================

DSA_SYSTEM_PROMPT = """你是 DSA（Daily Stock Analysis），Frank 的专属 A 股研究分析师。

你的身份：
- 你是一个有独立思考能力的分析师，不是数据查询机器
- 你有自己的判断和观点，会主动建议、指出风险、甚至质疑
- 你是 Frank 的同事，语气是专业分析师对基金经理汇报——尊重但有独立思考
- Frank 是老大，最终决策权在他，但你敢于说不同意见

你的分析框架：
1. 技术面：趋势（MA排列）/ 乖离率 / 量能 / MACD / 布林线
2. 基本面：PE / PB / 股息率 / 机构持仓
3. 行业：是否在当前主线 / 行业偏离度 / 板块强弱
4. 铁律：7条交易铁律检查（严进/顺势/筹码/回踩/一票否决/估值/强势放宽）

你的对话原则：
- 有观点，不是数据播报员。每个分析都给出自己的判断
- 每条结论引用数据来源
- 主动建议、指出风险
- 信息不够时坦诚说"数据不足"，不要编造
- 结论先行，细节按需展开
- 用自然语言，不用 JSON，不用 Markdown
- 每次回复大约 200-400 字，像跟同事口头汇报
- 说中文

你可以调用工具获取数据。拿到数据后，用你的分析框架形成观点再回复。"""

# ============================================================
# OpenAI Function Calling 工具定义
# ============================================================

DSA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tushare_daily",
            "description": "获取股票日K线数据（开高低收+成交量）。用于分析趋势和计算技术指标。",
            "parameters": {
                "type": "object",
                "properties": {
                    "stock_code": {"type": "string", "description": "股票代码，如 600519"},
                    "limit": {"type": "integer", "description": "返回条数，默认60"}
                },
                "required": ["stock_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tushare_daily_basic",
            "description": "获取股票每日指标：PE(TTM)、PB、股息率(dv_ratio)、换手率、总市值。用于基本面分析。",
            "parameters": {
                "type": "object",
                "properties": {
                    "stock_code": {"type": "string", "description": "股票代码，如 600519"},
                    "limit": {"type": "integer", "description": "返回条数，默认5"}
                },
                "required": ["stock_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tushare_stk_mins",
            "description": "获取股票分钟K线。用于短线分析和抓拐点。freq可选：1min/5min/15min/30min/60min",
            "parameters": {
                "type": "object",
                "properties": {
                    "stock_code": {"type": "string", "description": "股票代码"},
                    "freq": {"type": "string", "description": "频率：1min/5min/15min/30min/60min"},
                    "limit": {"type": "integer", "description": "返回条数，默认60"}
                },
                "required": ["stock_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "legacy_market_overview",
            "description": "获取当日A股大盘多空分析，含35信号行业排名（多头/空头持续天数）、行业转换动态。这是判断主线方向的核心数据。",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "legacy_stock_detail",
            "description": "获取个股详情（140+字段），含涨跌幅、成交量、MA、布林线、行业排名、当日个股总分等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "stock_code": {"type": "string", "description": "股票代码或名称"}
                },
                "required": ["stock_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "legacy_indexes",
            "description": "获取上证/深证/创业板三大指数实时数据。",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "legacy_hot_industries",
            "description": "获取当日涨停股票数量最多的前5个行业。",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "news_search",
            "description": "搜索最新新闻。用于查找个股/行业/宏观相关新闻，获取信息来源链接。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "freshness": {"type": "string", "description": "时效：oneDay/oneWeek/oneMonth"}
                },
                "required": ["query"]
            }
        }
    },
]

# ============================================================
# 工具执行器
# ============================================================

def execute_tool(name: str, args: dict) -> str:
    """执行一个工具调用，返回 JSON 字符串结果。"""
    try:
        if name == "tushare_daily":
            r = ts.get_daily(args["stock_code"], args.get("limit", 60))
        elif name == "tushare_daily_basic":
            r = ts.get_daily_basic(args["stock_code"], args.get("limit", 5))
        elif name == "tushare_stk_mins":
            r = ts.get_stk_mins(args["stock_code"], args.get("freq", "60min"), args.get("limit", 60))
        elif name == "legacy_market_overview":
            r = legacy.get_market_overview()
        elif name == "legacy_stock_detail":
            r = legacy.get_stock_detail(args["stock_code"])
        elif name == "legacy_indexes":
            r = legacy.get_indexes()
        elif name == "legacy_hot_industries":
            r = legacy.get_hot_industries()
        elif name == "news_search":
            r = news.search_news(args["query"], freshness=args.get("freshness", "oneWeek"))
        else:
            r = {"success": False, "error": f"unknown tool: {name}"}
        return json.dumps(r, ensure_ascii=False, default=str)[:6000]
    except Exception as exc:
        logger.exception("tool %s failed", name)
        return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)


# ============================================================
# LLM 调用（OpenRouter，支持 function calling + SSE 流式）
# ============================================================

def _call_llm(messages: List[Dict], tools: list = None, stream: bool = False) -> Dict:
    settings = get_settings()
    payload = {
        "model": settings.DSA_PRIMARY_MODEL,
        "messages": messages,
        "temperature": 0.4,
        "stream": stream,
    }
    if tools:
        payload["tools"] = tools

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    models = [settings.DSA_PRIMARY_MODEL, settings.DSA_FALLBACK_MODEL]
    for model in models:
        payload["model"] = model
        try:
            if stream:
                resp = requests.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                                     headers=headers, json=payload, stream=True, timeout=60)
                resp.raise_for_status()
                return resp  # 返回 Response 对象供流式消费
            else:
                resp = requests.post(f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                                     headers=headers, json=payload, timeout=60)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("LLM call failed model=%s: %s", model, exc)
            continue
    return {"error": "all models failed"}


def run_dsa_agent(user_message: str, conversation_history: List[Dict] = None,
                   context_block: str = "", max_tool_rounds: int = 5) -> Generator[Dict, None, None]:
    """DSA Agent 主循环：LLM 推理 → 工具调用 → 流式回复。

    Yields:
        {"type": "chunk", "text": "..."} — 回复片段
        {"type": "tool_call", "name": "...", "args": {...}} — 工具调用记录
        {"type": "done", "full_text": "...", "data_sources": [...]} — 完成
    """
    system_content = DSA_SYSTEM_PROMPT
    if context_block:
        system_content += "\n\n[对话上下文]\n" + context_block
    messages = [{"role": "system", "content": system_content}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    data_sources = []

    for round_i in range(max_tool_rounds):
        data = _call_llm(messages, tools=DSA_TOOLS)

        if isinstance(data, dict) and "error" in data:
            yield {"type": "chunk", "text": f"[DSA 连接异常: {data['error']}]"}
            yield {"type": "done", "full_text": "", "data_sources": []}
            return

        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        tool_calls = msg.get("tool_calls")

        if not tool_calls:
            # 没有工具调用 — 流式输出最终回复
            content = msg.get("content", "")
            # 逐段输出（模拟流式）
            chunk_size = 20
            for i in range(0, len(content), chunk_size):
                yield {"type": "chunk", "text": content[i:i+chunk_size]}
            yield {"type": "done", "full_text": content, "data_sources": data_sources}
            return

        # 有工具调用 — 执行并继续
        messages.append(msg)
        for tc in tool_calls:
            func_name = tc["function"]["name"]
            try:
                func_args = json.loads(tc["function"]["arguments"] or "{}")
            except Exception:
                func_args = {}

            yield {"type": "tool_call", "name": func_name, "args": func_args}

            result = execute_tool(func_name, func_args)
            data_sources.append(f"tool:{func_name}")

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result[:5000],
            })

    yield {"type": "chunk", "text": "分析太复杂了，我需要更多时间思考。"}
    yield {"type": "done", "full_text": "", "data_sources": data_sources}


# ============================================================
# API 接口
# ============================================================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict] = None
    conversation_history: Optional[List[Dict]] = None
    context_block: Optional[str] = None


class AnalyzeRequest(BaseModel):
    stock_code: str
    question: Optional[str] = None


@app.get("/health")
def health():
    settings = get_settings()
    return {"status": "ok", "service": "dsa-agent", "configured": settings.is_configured}


@app.post("/chat")
async def chat(req: ChatRequest):
    """DSA 核心接口 — Frank 跟 DSA 对话（SSE 流式）。"""
    def event_stream():
        full_text = ""
        for event in run_dsa_agent(
            req.message,
            conversation_history=req.conversation_history,
            context_block=req.context_block or "",
        ):
            if event["type"] == "chunk":
                full_text += event.get("text", "")
                yield f"event: chunk\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            elif event["type"] == "tool_call":
                yield f"event: tool_call\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            elif event["type"] == "done":
                event["full_text"] = full_text or event.get("full_text", "")
                yield f"event: done\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """个股深度诊断。"""
    question = req.question or f"{req.stock_code} 你怎么看？能碰吗？"
    prompt = f"请分析 {req.stock_code}。{question}"

    def event_stream():
        full_text = ""
        for event in run_dsa_agent(prompt):
            if event["type"] == "chunk":
                full_text += event.get("text", "")
                yield f"event: chunk\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            elif event["type"] == "tool_call":
                yield f"event: tool_call\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            elif event["type"] == "done":
                event["full_text"] = full_text or event.get("full_text", "")
                yield f"event: done\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/market_brief")
async def market_brief():
    """当日市场报告（有观点+新闻来源的晨报）。"""
    prompt = """请生成今日市场报告。要求：
1. 先调 legacy_market_overview 拿多空分析和行业排名
2. 再调 legacy_indexes 拿三大指数
3. 再调 legacy_hot_industries 拿涨停行业
4. 对主线行业调 news_search 搜相关新闻
5. 综合以上数据，用你的分析师视角，输出一份有观点的晨报

报告格式要求：
- 今日主线研判（3条主线+为什么是主线）
- 新增方向预警（有没有新转多头的行业）
- 风险信号（转空的行业+过热的行业）
- 市场情绪（指数+成交+VIX）
- Top5个股简评
- 每条分析引用数据来源和新闻链接
- 最后给你的观点总结"""

    def event_stream():
        full_text = ""
        for event in run_dsa_agent(prompt):
            if event["type"] == "chunk":
                full_text += event.get("text", "")
                yield f"event: chunk\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            elif event["type"] == "tool_call":
                yield f"event: tool_call\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            elif event["type"] == "done":
                event["full_text"] = full_text or event.get("full_text", "")
                yield f"event: done\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    logger.info("DSA Agent 启动: http://%s:%d", settings.DSA_HOST, settings.DSA_PORT)
    uvicorn.run(app, host=settings.DSA_HOST, port=settings.DSA_PORT)
