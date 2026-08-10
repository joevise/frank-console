# -*- coding: utf-8 -*-
"""上下文压缩器 — 从对话历史中提取核心结论，防止上下文爆炸。"""
from __future__ import annotations

import json
import logging
from typing import List, Dict, Optional
import requests
import os

logger = logging.getLogger(__name__)


def _summarize_with_llm(messages: List[Dict], max_chars: int = 500) -> str:
    """用轻量 LLM 压缩对话历史。"""
    # 构建对话文本
    dialogue = []
    for m in messages[-10:]:  # 只取最近10条
        role = m.get("role", "?")
        source = m.get("source", "")
        content = m.get("content", "")[:200]  # 每条最多200字
        prefix = f"{role}({source})" if source else role
        dialogue.append(f"{prefix}: {content}")

    dialogue_text = "\n".join(dialogue)

    prompt = f"""请将以下对话历史压缩成一段不超过{max_chars}字的核心上下文摘要。
保留：关键结论、用户意图、已分析过的股票、重要的判断和建议。
去掉：客套话、重复信息、细节数据。

对话历史：
{dialogue_text}

核心上下文摘要（{max_chars}字以内）："""

    # 用 DSA Agent 的 LLM（同一个 OpenRouter key）
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        # 没有 key，用简单的规则压缩
        return _rule_based_compress(messages, max_chars)

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek/deepseek-v4-flash",  # 用最快的模型做压缩
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.3,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        summary = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return summary.strip()[:max_chars]
    except Exception as exc:
        logger.warning("LLM summarize failed: %s", exc)
        return _rule_based_compress(messages, max_chars)


def _rule_based_compress(messages: List[Dict], max_chars: int = 500) -> str:
    """无 LLM 的规则压缩（降级方案）。"""
    lines = []
    total = 0
    for m in messages[-8:]:
        role = m.get("role", "?")
        source = m.get("source", "")
        content = m.get("content", "")
        # 每条消息只取前80字
        if len(content) > 80:
            content = content[:80] + "..."
        prefix = source.upper() if source else role
        line = f"[{prefix}] {content}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)
    return "\n".join(lines)


def build_context_block(
    messages: List[Dict],
    user_message: str,
    use_llm: bool = True,
) -> str:
    """从对话历史构建压缩上下文 block。

    Args:
        messages: 本次对话的所有历史消息
        user_message: 当前用户问题
        use_llm: 是否用 LLM 压缩（True）或规则压缩（False）

    Returns:
        压缩后的上下文字符串，适合传给 DSA 或 Frank
    """
    if not messages or len(messages) <= 1:
        return ""

    # 排除当前用户消息（避免重复）
    history = [m for m in messages if m.get("content") != user_message]

    if not history:
        return ""

    if use_llm:
        return _summarize_with_llm(history, max_chars=500)
    return _rule_based_compress(history, max_chars=500)


def build_dsa_history(messages: List[Dict], max_messages: int = 6) -> List[Dict]:
    """从对话历史构建 DSA 的 conversation_history 参数。

    返回最近 N 条消息，格式为 OpenAI messages 格式。
    DSA 可以看到 Frank 和自己之前的对话。
    """
    recent = messages[-max_messages:] if len(messages) > max_messages else messages

    history = []
    for m in recent:
        role = m.get("role", "user")
        content = m.get("content", "")
        source = m.get("source", "")

        # 标注来源，让 DSA 知道是谁说的
        if source and source != "dsa":
            content = f"[{source}说] {content}"

        history.append({"role": role, "content": content})

    return history
