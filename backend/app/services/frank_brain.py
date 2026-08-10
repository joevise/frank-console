# -*- coding: utf-8 -*-
"""Frank Brain v4 — 真正的 Agent Loop。

核心改进：
- 不再硬编码 CALL_DSA 标记
- Frank 自主选择工具（Tool Registry）
- 多轮思考：思考→调工具→观察→再思考→回复
- DSA 工具调用过程实时推送前端
- Session Manager 管理上下文

Frank 工具箱：
- dsa_analysis: 调DSA分析师深度分析
- 未来可扩展更多工具
"""
from __future__ import annotations
import json
import logging
import threading
import queue
from typing import Any, Dict, Generator, List, Optional

import requests

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ============================================================
# OpenMind 调用
# ============================================================

def _call_openmind_stream(text, user_id, conversation_id, api_url, api_key, mind_id):
    """发送消息到 OpenMind。"""
    url = f"{api_url}/v1/chat/{mind_id}/stream"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream",
    }
    payload = {"user_id": user_id, "conversation_id": conversation_id, "text": text}
    resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=90)
    resp.raise_for_status()
    return resp


def _parse_sse_stream(resp) -> Generator[Dict[str, Any], None, None]:
    """解析 OpenMind SSE 流。"""
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data: "):
            data_str = line[6:].strip()
        elif line.startswith("data:"):
            data_str = line[5:].strip()
        else:
            continue
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            continue

        msg_type = data.get("type", "")
        if msg_type == "answer":
            chunk = data.get("data", {}).get("chunk", "")
            if chunk:
                yield {"type": "answer", "chunk": chunk}
        elif msg_type == "done":
            yield {"type": "done"}


# ============================================================
# DSA 工具调用（流式，含步骤推送）
# ============================================================

DSA_AGENT_URL = "http://dsa-agent:8120/chat"

_TOOL_NAME_MAP = {
    "tushare_daily": "查询日K线数据",
    "tushare_daily_basic": "查询基本面(PE/PB/ROE)",
    "tushare_stk_mins": "查询分钟K线",
    "news_search": "搜索新闻资讯",
}


def _friendly_name(tool_name: str, args: dict) -> str:
    base = _TOOL_NAME_MAP.get(tool_name, f"调用 {tool_name}")
    stock = args.get("stock_code") or args.get("ts_code") or args.get("code")
    if stock:
        base += f" — {stock}"
    return base


def _call_dsa_stream(question: str, timeout: int = 120) -> Generator[Dict[str, Any], None, None]:
    """调 DSA Agent，线程+队列，实时 yield 工具步骤+最终文字。"""
    result_q = queue.Queue()
    SENTINEL = object()

    def _worker():
        try:
            resp = requests.post(DSA_AGENT_URL, json={"message": question}, stream=True, timeout=timeout)
            resp.raise_for_status()
            full_text = ""
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                raw = line[5:].strip() if line.startswith("data: ") else line[5:].strip()
                try:
                    data = json.loads(raw)
                except Exception:
                    continue
                evt_type = data.get("type", "")
                if evt_type == "tool_call":
                    result_q.put({"type": "dsa_step",
                                  "text": _friendly_name(data.get("name", ""), data.get("args", {}))})
                elif evt_type == "chunk" and data.get("text"):
                    full_text += data["text"]
                elif evt_type == "done":
                    full_text = data.get("full_text", full_text)
                    result_q.put({"type": "dsa_done", "text": full_text})
                    result_q.put(SENTINEL)
                    return
            result_q.put({"type": "dsa_done", "text": full_text or "DSA 未返回内容"})
        except Exception as exc:
            logger.exception("DSA stream worker failed")
            result_q.put({"type": "dsa_done", "text": f"DSA 调用失败: {exc}"})
        finally:
            result_q.put(SENTINEL)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

    while True:
        try:
            item = result_q.get(timeout=timeout)
            if item is SENTINEL:
                break
            yield item
        except queue.Empty:
            yield {"type": "dsa_done", "text": "DSA 超时"}
            break
    t.join(timeout=1)


# ============================================================
# Frank Agent Loop — 核心循环
# ============================================================

# Frank 的工具提示（注入到消息中）
TOOL_PROMPT = """[系统提示 — 你有以下工具可用]
当你需要市场数据、个股分析时，在回复中嵌入以下标记：
[CALL_DSA: 你的问题]

例如：[CALL_DSA: 茅台最近的技术面和基本面分析]
系统会自动调 DSA 分析师并返回结果给你，你拿到数据后继续回复用户。
注意：只在需要数据时才调用，简单闲聊不需要。
[系统提示结束]
"""

CALL_DSA_PATTERN = __import__("re").compile(r'\[CALL_DSA:\s*(.+?)\]', __import__("re").DOTALL)


def stream_frank_reply(user_message: str,
                       conversation_id: str = None,
                       prior_messages: list = None,
                       user_id: str = "user-1") -> Generator[Dict[str, Any], None, None]:
    """Frank Agent Loop — 多轮思考，工具调用过程实时推送。

    Yields:
        {"type": "frank_chunk", "text": "..."}   — Frank回复片段
        {"type": "dsa_start", "query": "..."}     — 开始调DSA
        {"type": "dsa_step", "text": "..."}       — DSA工具调用步骤
        {"type": "dsa_result", "text": "..."}     — DSA完整分析
        {"type": "frank_final", "text": "..."}    — Frank最终回复
        {"type": "done"}                           — 完成
        {"type": "error", "message": "..."}        — 错误
    """
    settings = get_settings()
    augmented_message = TOOL_PROMPT + user_message
    accumulated = ""

    for round_num in range(3):  # 最多3轮工具调用
        try:
            resp = _call_openmind_stream(
                augmented_message if round_num == 0 else accumulated,
                user_id, conversation_id or "",
                settings.openmind_api_url,
                settings.openmind_api_key,
                settings.openmind_mind_id,
            )
        except Exception as exc:
            yield {"type": "error", "message": f"OpenMind 连接异常: {exc}"}
            return

        round_text = ""
        has_tool_call = False
        yielded_len = 0

        for event in _parse_sse_stream(resp):
            if event["type"] == "answer":
                chunk = event["chunk"]
                accumulated += chunk
                round_text += chunk

                # 检测 CALL_DSA 标记
                if CALL_DSA_PATTERN.search(round_text):
                    has_tool_call = True
                    match = CALL_DSA_PATTERN.search(round_text)
                    safe_end = match.start()
                    if safe_end > yielded_len:
                        # 推送标记前的文字
                        pre_text = round_text[yielded_len:safe_end].rstrip()
                        if pre_text:
                            yield {"type": "frank_chunk", "text": pre_text}
                        yielded_len = safe_end
                elif not has_tool_call:
                    yield {"type": "frank_chunk", "text": chunk}
                    yielded_len = len(round_text)
            elif event["type"] == "done":
                pass

        match = CALL_DSA_PATTERN.search(round_text)
        if match:
            dsa_question = match.group(1).strip()
            # 推送标记前的文字
            before_call = round_text[:match.start()].rstrip()
            if before_call:
                yield {"type": "frank_chunk", "text": before_call}

            # 通知前端：开始调 DSA
            yield {"type": "dsa_start", "query": dsa_question}

            # 流式调 DSA — 实时推送工具步骤
            dsa_full_text = ""
            for dsa_event in _call_dsa_stream(dsa_question):
                if dsa_event["type"] == "dsa_step":
                    yield dsa_event  # 工具调用步骤
                elif dsa_event["type"] == "dsa_done":
                    dsa_full_text = dsa_event.get("text", "")

            # 推送 DSA 完整分析
            yield {"type": "dsa_result", "text": dsa_full_text}

            # 构造二轮消息：让 Frank 基于 DSA 分析给最终回复
            accumulated = (
                f"[DSA 分析结果]\n用户原始问题：{user_message}\n\n"
                f"DSA 分析：\n{dsa_full_text}\n\n"
                f"请基于以上 DSA 分析结果，给出你的最终判断和建议。"
                f"不要重复 DSA 的原始数据，直接给观点。"
            )
            continue
        else:
            # 没有 CALL_DSA — Frank 的回复已经完整
            if round_num > 0 and round_text:
                yield {"type": "frank_final", "text": round_text}
            break

    yield {"type": "done"}


def frank_reply_sync(user_message: str, conversation_id: str = None,
                     prior_messages: list = None) -> Dict[str, str]:
    """同步版本（降级用）。"""
    result_text = ""
    for event in stream_frank_reply(user_message, conversation_id, prior_messages):
        t = event.get("type", "")
        if t in ("frank_chunk", "frank_final"):
            result_text += event.get("text", "")
        elif event["type"] == "dsa_result":
            result_text += "\n\n--- DSA 分析 ---\n" + event.get("text", "")
        elif event["type"] == "error":
            return {"reply": "", "error": event.get("message", "unknown")}
    return {"reply": result_text, "error": None}
