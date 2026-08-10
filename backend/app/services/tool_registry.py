# -*- coding: utf-8 -*-
"""Tool Registry — 工具注册表。

Frank 和 DSA 共用同一套工具系统。
加新工具只需注册一行，Agent自主选择调用。
"""
from __future__ import annotations
import json
import logging
import threading
import queue
from typing import Any, Callable, Dict, Generator, List, Optional

import requests

logger = logging.getLogger(__name__)


# ============================================================
# 工具定义
# ============================================================

class Tool:
    """单个工具定义。"""
    def __init__(self, name: str, description: str, handler: Callable,
                 parameters: dict = None, friendly_name: str = None):
        self.name = name
        self.description = description
        self.handler = handler
        self.parameters = parameters or {"type": "object", "properties": {}}
        self.friendly_name = friendly_name or name

    def to_openai_format(self) -> dict:
        """转为 OpenAI function calling 格式。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

    def execute(self, args: dict) -> str:
        """执行工具，返回字符串结果。"""
        try:
            result = self.handler(**args)
            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False, default=str)[:5000]
        except Exception as e:
            logger.exception("Tool %s failed", self.name)
            return f"工具执行失败: {e}"


class ToolRegistry:
    """工具注册表 — 管理所有可用工具。"""
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_names(self) -> List[str]:
        return list(self._tools.keys())

    def to_openai_format(self, names: List[str] = None) -> List[dict]:
        if names is None:
            names = list(self._tools.keys())
        return [self._tools[n].to_openai_format() for n in names if n in self._tools]

    def execute(self, name: str, args: dict) -> str:
        tool = self.get(name)
        if not tool:
            return f"未知工具: {name}"
        return tool.execute(args)


# ============================================================
# 全局注册表
# ============================================================

registry = ToolRegistry()


# ============================================================
# 工具实现 — Frank 可用的工具
# ============================================================

DSA_AGENT_URL = "http://dsa-agent:8120/chat"


def _call_dsa_tool(question: str, **kwargs) -> str:
    """调 DSA 分析师做深度分析。返回分析文字。"""
    full_text = ""
    try:
        resp = requests.post(DSA_AGENT_URL, json={"message": question}, stream=True, timeout=120)
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            raw = line[5:].strip() if line.startswith("data: ") else line[5:].strip()
            try:
                data = json.loads(raw)
                if data.get("type") == "chunk" and data.get("text"):
                    full_text += data["text"]
                elif data.get("type") == "done":
                    full_text = data.get("full_text", full_text)
            except Exception:
                pass
    except Exception as e:
        logger.warning("DSA tool failed: %s", e)
        return f"DSA 分析暂不可用: {e}"
    return full_text or "DSA 未返回内容"


def _call_dsa_stream_tool(question: str, **kwargs) -> Generator[dict, None, None]:
    """调 DSA 分析师，流式返回（含工具调用过程）。
    用于 Agent Loop 中实时推送 DSA 的工具调用步骤。
    """
    try:
        resp = requests.post(DSA_AGENT_URL, json={"message": question}, stream=True, timeout=120)
        resp.raise_for_status()
        full_text = ""
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            raw = line[5:].strip() if line.startswith("data: ") else line[5:].strip()
            try:
                data = json.loads(raw)
                evt_type = data.get("type", "")
                if evt_type == "tool_call":
                    yield {"type": "tool_step", "name": data.get("name", ""),
                           "text": _friendly_name(data.get("name", ""), data.get("args", {}))}
                elif evt_type == "chunk" and data.get("text"):
                    full_text += data["text"]
                elif evt_type == "done":
                    full_text = data.get("full_text", full_text)
            except Exception:
                pass
        yield {"type": "done", "text": full_text}
    except Exception as e:
        logger.warning("DSA stream tool failed: %s", e)
        yield {"type": "done", "text": f"DSA 分析暂不可用: {e}"}


_TOOL_NAME_MAP = {
    "tushare_daily": "查询日K线数据",
    "tushare_daily_basic": "查询基本面(PE/PB/ROE)",
    "tushare_stk_mins": "查询分钟K线",
    "news_search": "搜索新闻资讯",
    "legacy_market_overview": "查询大盘多空",
    "legacy_stock_detail": "查询个股详情",
    "legacy_indexes": "查询指数",
    "legacy_hot_industries": "查询热门行业",
}


def _friendly_name(tool_name: str, args: dict) -> str:
    base = _TOOL_NAME_MAP.get(tool_name, f"调用 {tool_name}")
    stock = args.get("stock_code") or args.get("ts_code") or args.get("code")
    if stock:
        base += f" — {stock}"
    return base


# ============================================================
# 注册 Frank 的工具
# ============================================================

registry.register(Tool(
    name="dsa_analysis",
    description="调DSA分析师做深度市场/个股分析。当需要K线、基本面、技术面、行业判断时使用。返回详细分析报告。",
    handler=_call_dsa_tool,
    parameters={
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "要分析的问题，如'茅台技术面分析'"}
        },
        "required": ["question"]
    },
    friendly_name="DSA深度分析"
))

# 未来可注册更多工具：
# registry.register(Tool(name="image_analyze", ...))
# registry.register(Tool(name="web_search", ...))
# registry.register(Tool(name="report_generate", ...))
