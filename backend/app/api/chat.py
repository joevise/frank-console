# -*- coding: utf-8 -*-
"""Chat API v2 — Session 管理 + Agent Loop。

新增：
- GET  /api/chat/sessions — 会话列表
- POST /api/chat/sessions — 创建新会话
- DELETE /api/chat/sessions/{id} — 删除会话
- PATCH /api/chat/sessions/{id} — 重命名
- POST /api/chat/stream — 流式对话（Agent Loop）
- POST /api/chat/dsa/chat — 直接跟DSA聊
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models.models import Conversation, Message, User
from app.services.session_manager import SessionManager
from app.services.frank_brain import stream_frank_reply, frank_reply_sync

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

DSA_AGENT_URL = "http://dsa-agent:8120/chat"


# ============================================================
# Models
# ============================================================

class SendMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    attachments: Optional[List[dict]] = None


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


class RenameSessionRequest(BaseModel):
    title: str


# ============================================================
# Session CRUD
# ============================================================

@router.get("/sessions")
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """列出用户的所有对话。"""
    sm = SessionManager(db)
    return sm.list_sessions(str(current_user.id))


@router.post("/sessions")
def create_session(
    req: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建新对话。"""
    sm = SessionManager(db)
    conv = sm.create_session(str(current_user.id), req.title)
    return {"id": conv.id, "title": conv.title, "source": conv.source}


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除对话。"""
    sm = SessionManager(db)
    if sm.delete_session(session_id, str(current_user.id)):
        return {"ok": True}
    raise HTTPException(404, "对话不存在")


@router.patch("/sessions/{session_id}")
def rename_session(
    session_id: str,
    req: RenameSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """重命名对话。"""
    sm = SessionManager(db)
    sm.update_title(session_id, req.title)
    return {"ok": True}


# ============================================================
# 消息历史
# ============================================================

@router.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取对话的所有消息。"""
    sm = SessionManager(db)
    conv = sm.get_session(session_id, str(current_user.id))
    if not conv:
        raise HTTPException(404, "对话不存在")
    messages = sm.get_messages(session_id)
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "source": m.source,
            "tool_calls": m.tool_calls,
            "created_at": m.created_at.isoformat() if m.created_at else "",
        }
        for m in messages
    ]


# ============================================================
# 对话流（Agent Loop）
# ============================================================

@router.post("/stream")
async def chat_stream(
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Frank 对话（SSE 流式）— Agent Loop + DSA 工具过程实时推送。"""
    sm = SessionManager(db)
    user_id = str(current_user.id)

    # 创建或获取对话
    if req.conversation_id:
        conv = sm.get_session(req.conversation_id, user_id)
        if not conv:
            raise HTTPException(404, "对话不存在")
        conv_id = conv.id
    else:
        conv = sm.create_session(user_id)
        conv_id = conv.id

    # 存用户消息
    sm.add_message(conv_id, "user", req.message)

    # 自动标题（第一条消息）
    if conv.title == "新对话":
        sm.auto_title(conv_id, req.message)

    # 构建上下文
    prior_messages = sm.build_context(conv_id)

    # 流式生成
    def generate():
        frank_text = ""
        dsa_text = ""
        steps = []

        try:
            for event in stream_frank_reply(
                req.message,
                conversation_id=conv_id,
                prior_messages=prior_messages,
                user_id=user_id,
            ):
                evt_type = event.get("type", "")

                if evt_type == "frank_chunk":
                    frank_text += event.get("text", "")
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                elif evt_type == "dsa_start":
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                elif evt_type == "dsa_step":
                    steps.append(event.get("text", ""))
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                elif evt_type == "dsa_result":
                    dsa_text = event.get("text", "")
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                elif evt_type == "frank_final":
                    frank_text += event.get("text", "")
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                elif evt_type == "error":
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                elif evt_type == "done":
                    # 存 Frank 回复到 DB
                    if frank_text:
                        sm.add_message(conv_id, "assistant", frank_text, source="frank",
                                       tool_calls={"dsa_steps": steps, "dsa_analysis": dsa_text} if dsa_text else None)
                    # 发送 conversation_id
                    done_data = {"type": "done", "conversation_id": conv_id}
                    yield f"data: {json.dumps(done_data, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.exception("Stream error")
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ============================================================
# 兼容旧 API（避免前端突然断）
# ============================================================

@router.post("/send")
def send_message(
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """同步发送消息（降级用）。"""
    sm = SessionManager(db)
    user_id = str(current_user.id)

    if req.conversation_id:
        conv_id = req.conversation_id
    else:
        conv = sm.create_session(user_id)
        conv_id = conv.id

    sm.add_message(conv_id, "user", req.message)

    prior = sm.build_context(conv_id)
    result = frank_reply_sync(req.message, conv_id, prior)

    if result.get("reply"):
        sm.add_message(conv_id, "assistant", result["reply"], source="frank")

    return {"reply": result["reply"], "error": result.get("error"),
            "conversation_id": conv_id}


@router.get("/conversations")
def list_conversations(
    source: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """兼容旧接口 — 返回会话列表。"""
    sm = SessionManager(db)
    return sm.list_sessions(str(current_user.id))


@router.get("/conversations/{conv_id}/messages")
def get_conv_messages(
    conv_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """兼容旧接口。"""
    return get_messages(conv_id, current_user, db)


@router.delete("/conversations/{conv_id}")
def delete_conv(
    conv_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """兼容旧接口。"""
    sm = SessionManager(db)
    if sm.delete_session(conv_id, str(current_user.id)):
        return {"ok": True}
    raise HTTPException(404, "对话不存在")


# ============================================================
# DSA 直聊
# ============================================================

@router.post("/dsa/chat")
def dsa_chat(message: str, current_user: User = Depends(get_current_user)):
    """直接跟 DSA 聊天（非流式，简单接口）。"""
    try:
        resp = requests.post(DSA_AGENT_URL, json={"message": message}, timeout=120)
        resp.raise_for_status()
        full_text = ""
        for line in resp.text.split("\n"):
            if line.startswith("data:"):
                try:
                    data = json.loads(line[5:].strip())
                    if data.get("type") == "done":
                        full_text = data.get("full_text", "")
                    elif data.get("type") == "chunk" and data.get("text"):
                        full_text += data["text"]
                except Exception:
                    pass
        return {"reply": full_text, "error": None}
    except Exception as exc:
        return {"reply": "", "error": str(exc)}
