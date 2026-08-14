# -*- coding: utf-8 -*-
"""DSA Agent API Server v2 — 精简版。
只用 tushare + news_search，走 OpenRouter function calling。
"""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, Generator, List

import requests
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="DSA Agent", version="2.0")

# ============================================================
# 配置
# ============================================================

DSA_SYSTEM_PROMPT = """你是 DSA（深度证券分析师），Frank 的专属数据分析师。

你的职责：
1. 用工具获取实时市场数据（K线、基本面、新闻）
2. 基于数据做客观的技术面和基本面分析
3. 给出数据支撑的判断，不加感情色彩

规则：
- 先调工具拿数据，再分析
- 最多调用5轮工具
- 最后一轮必须给出文字总结
- 数据来源标注清楚
"""

# ============================================================
# 工具定义（OpenAI function calling 格式）
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
            "description": "获取股票每日指标：PE(TTM)、PB、股息率、换手率、总市值。用于基本面分析。",
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
            "description": "获取股票分钟K线。用于短线分析和抓拐点。",
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
            "name": "index_daily",
            "description": "获取大盘指数日K线。用于分析大盘走势。支持的指数：000001.SH(上证综指)、399001.SZ(深证成指)、399006.SZ(创业板指)、000300.SH(沪深300)、000905.SH(中证500)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "index_code": {"type": "string", "description": "指数代码，如 000001.SH"},
                    "limit": {"type": "integer", "description": "返回条数，默认30"}
                },
                "required": ["index_code"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "news_search",
            "description": "搜索新闻资讯。用于获取个股/行业/宏观的最新新闻。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "days": {"type": "integer", "description": "搜索最近N天，默认3"}
                },
                "required": ["query"]
            }
        }
    }
]


# ============================================================
# 工具执行
# ============================================================

def execute_tool(name: str, args: dict) -> str:
    """执行工具调用。"""
    try:
        if name == "tushare_daily":
            from dsa_agent.data.tushare_client import get_daily
            return json.dumps(get_daily(args.get("stock_code", ""), limit=args.get("limit", 60)), ensure_ascii=False)
        elif name == "tushare_daily_basic":
            from dsa_agent.data.tushare_client import get_daily_basic
            return json.dumps(get_daily_basic(args.get("stock_code", ""), limit=args.get("limit", 5)), ensure_ascii=False)
        elif name == "tushare_stk_mins":
            from dsa_agent.data.tushare_client import get_stk_mins
            return json.dumps(get_stk_mins(args.get("stock_code", ""), freq=args.get("freq", "30min"), limit=args.get("limit", 60)), ensure_ascii=False)
        elif name == "index_daily":
            from dsa_agent.data.tushare_client import get_index_daily
            return json.dumps(get_index_daily(args.get("index_code", "000001.SH"), limit=args.get("limit", 30)), ensure_ascii=False)
        elif name == "news_search":
            from dsa_agent.search.news_search import search_news
            return json.dumps(search_news(args.get("query", ""), max_results=5, freshness="oneWeek"), ensure_ascii=False)
    except Exception as e:
        logger.exception("Tool %s failed", name)
        return f"工具执行失败: {e}"
    return f"未知工具: {name}"


# ============================================================
# LLM 调用（OpenRouter）
# ============================================================

def _call_llm(messages, tools=None):
    """调用 LLM (OpenRouter) 获取回复或工具调用。"""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    base_url = "https://openrouter.ai/api/v1"
    model = os.environ.get("DSA_PRIMARY_MODEL", "xiaomi/mimo-v2.5")
    fallback = os.environ.get("DSA_FALLBACK_MODEL", "deepseek/deepseek-v4-flash")

    payload = {"model": model, "messages": messages, "temperature": 0.3}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for m in [model, fallback]:
        payload["model"] = m
        try:
            resp = requests.post(f"{base_url}/chat/completions", json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            logger.warning("LLM %s returned %d: %s", m, resp.status_code, resp.text[:200])
        except Exception as e:
            logger.warning("LLM %s failed: %s", m, e)
    return {"error": "LLM 调用失败"}


# ============================================================
# DSA Agent 主循环
# ============================================================

TOOL_CALL_XML_PATTERN = __import__("re").compile(
    r"<tool_call>\s*<function=([^>]+)>(.*?)</function>\s*</tool_call>",
    __import__("re").DOTALL,
)
PARAM_XML_PATTERN = __import__("re").compile(
    r"<parameter=([^>]+)>(.*?)(?:</parameter>|(?=<parameter=)|(?=</function>))",
    __import__("re").DOTALL,
)


def _parse_tool_call_xml(content: str):
    """兜底：部分模型不走 function calling 协议，而是输出 <tool_call> XML 文本。
    解析后转成标准 tool_calls 走正常流程。"""
    calls = []
    for m in TOOL_CALL_XML_PATTERN.finditer(content):
        name = m.group(1).strip()
        body = m.group(2)
        args = {}
        for pm in PARAM_XML_PATTERN.finditer(body):
            args[pm.group(1).strip()] = pm.group(2).strip()
        calls.append({"name": name, "args": args})
    return calls


def run_dsa_agent(user_message: str, conversation_history: List[Dict] = None,
                   max_tool_rounds: int = 5) -> Generator[Dict, None, None]:
    """DSA Agent 主循环：LLM 推理 → 工具调用 → 流式回复。"""
    messages = [{"role": "system", "content": DSA_SYSTEM_PROMPT}]
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
        tool_calls = msg.get("tool_calls", [])

        # 兜底：模型把工具调用写成 <tool_call> XML 文本而非协议字段
        if not tool_calls:
            xml_calls = _parse_tool_call_xml(msg.get("content") or "")
            if xml_calls:
                logger.info("Parsed %d tool_call(s) from XML text: %s",
                            len(xml_calls), [c["name"] for c in xml_calls])
                tool_calls = [
                    {
                        "id": f"xmlcall-{round_i}-{i}",
                        "type": "function",
                        "function": {
                            "name": c["name"],
                            "arguments": json.dumps(c["args"], ensure_ascii=False),
                        },
                    }
                    for i, c in enumerate(xml_calls)
                ]
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls,
                })

        if tool_calls:
            # 有工具调用
            messages.append(msg)
            for tc in tool_calls:
                fn = tc.get("function", {})
                tool_name = fn.get("name", "")
                try:
                    tool_args = json.loads(fn.get("arguments", "{}"))
                except Exception:
                    tool_args = {}

                yield {"type": "tool_call", "name": tool_name, "args": tool_args}

                result = execute_tool(tool_name, tool_args)
                data_sources.append(tool_name)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": result[:3000],
                })
            # 继续下一轮
        else:
            # 无工具调用，输出文字
            content = msg.get("content", "")
            if content:
                yield {"type": "chunk", "text": content}
            yield {"type": "done", "full_text": content, "data_sources": data_sources}
            return

    # 超过最大轮数，强制要文字
    messages.append({"role": "system", "content": "已经收集了足够数据，请直接给出分析结论，不要再用工具。"})
    data = _call_llm(messages, tools=None)
    if isinstance(data, dict) and "choices" in data:
        content = data["choices"][0].get("message", {}).get("content", "")
        yield {"type": "chunk", "text": content}
        yield {"type": "done", "full_text": content, "data_sources": data_sources}
    else:
        yield {"type": "done", "full_text": "", "data_sources": data_sources}


# ============================================================
# API 端点
# ============================================================

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict] = None


@app.post("/chat")
async def chat(req: ChatRequest):
    def event_stream():
        try:
            for event in run_dsa_agent(req.message, req.conversation_history):
                yield f"data:{json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.exception("DSA stream error")
            yield f"data:{json.dumps({'type': 'done', 'full_text': f'DSA 内部错误: {e}', 'data_sources': []}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "dsa-agent", "tools": [t["function"]["name"] for t in DSA_TOOLS]}


# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8120)
