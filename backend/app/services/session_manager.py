# -*- coding: utf-8 -*-
"""Session Manager — 多会话/多话题/上下文压缩。

管理用户的多个对话：
- 创建/切换/删除对话
- 自动生成对话标题
- 上下文压缩（长对话自动摘要）
- 消息持久化（落库）
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session
from app.models.models import Conversation, Message, User

logger = logging.getLogger(__name__)

MAX_CONTEXT_MESSAGES = 10  # 超过10条开始压缩
COMPRESS_KEEP_HEAD = 3     # 压缩时保留前3条
COMPRESS_KEEP_TAIL = 5     # 压缩时保留后5条


class SessionManager:
    """对话会话管理器。"""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # 会话 CRUD
    # ============================================================

    def create_session(self, user_id: str, title: str = None) -> Conversation:
        """创建新对话。"""
        conv = Conversation(
            id=str(uuid4()),
            user_id=user_id,
            title=title or "新对话",
            source="frank",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def list_sessions(self, user_id: str, limit: int = 50) -> List[dict]:
        """列出用户的所有对话。"""
        convs = self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).limit(limit).all()

        result = []
        for c in convs:
            msg_count = self.db.query(Message).filter(
                Message.conversation_id == c.id
            ).count()
            last_msg = self.db.query(Message).filter(
                Message.conversation_id == c.id
            ).order_by(Message.created_at.desc()).first()

            result.append({
                "id": c.id,
                "title": c.title or "新对话",
                "source": c.source or "frank",
                "message_count": msg_count,
                "last_message": last_msg.content[:80] if last_msg else "",
                "last_time": (c.updated_at or c.created_at).isoformat() if c.updated_at else "",
            })
        return result

    def get_session(self, conv_id: str, user_id: str = None) -> Optional[Conversation]:
        """获取对话。"""
        q = self.db.query(Conversation).filter(Conversation.id == conv_id)
        if user_id:
            q = q.filter(Conversation.user_id == user_id)
        return q.first()

    def delete_session(self, conv_id: str, user_id: str) -> bool:
        """删除对话及其所有消息。"""
        conv = self.get_session(conv_id, user_id)
        if not conv:
            return False
        # 删消息
        self.db.query(Message).filter(Message.conversation_id == conv_id).delete()
        self.db.query(Conversation).filter(Conversation.id == conv_id).delete()
        self.db.commit()
        return True

    def update_title(self, conv_id: str, title: str):
        """更新对话标题。"""
        conv = self.db.query(Conversation).filter(Conversation.id == conv_id).first()
        if conv:
            conv.title = title[:200]
            conv.updated_at = datetime.utcnow()
            self.db.commit()

    def auto_title(self, conv_id: str, first_message: str):
        """从第一条消息自动生成标题。"""
        title = first_message[:30]
        if len(first_message) > 30:
            title += "..."
        self.update_title(conv_id, title)

    # ============================================================
    # 消息管理
    # ============================================================

    def add_message(self, conv_id: str, role: str, content: str,
                    source: str = "frank", tool_calls: dict = None) -> Message:
        """添加消息到对话。"""
        msg = Message(
            id=str(uuid4()),
            conversation_id=conv_id,
            role=role,
            content=content,
            source=source,
            tool_calls=tool_calls,
            created_at=datetime.utcnow(),
        )
        self.db.add(msg)
        # 更新对话时间
        conv = self.db.query(Conversation).filter(Conversation.id == conv_id).first()
        if conv:
            conv.updated_at = datetime.utcnow()
        self.db.commit()
        return msg

    def get_messages(self, conv_id: str, limit: int = 50) -> List[Message]:
        """获取对话的所有消息。"""
        return self.db.query(Message).filter(
            Message.conversation_id == conv_id
        ).order_by(Message.created_at.asc()).limit(limit).all()

    # ============================================================
    # 上下文构建（核心）
    # ============================================================

    def build_context(self, conv_id: str) -> List[dict]:
        """构建发给 LLM 的上下文消息列表。

        策略：
        - <= MAX_CONTEXT_MESSAGES: 全量
        - > MAX_CONTEXT_MESSAGES: 前3条 + 压缩摘要 + 后5条
        """
        messages = self.get_messages(conv_id, limit=100)
        if not messages:
            return []

        msg_dicts = [{"role": m.role, "content": m.content} for m in messages]

        if len(msg_dicts) <= MAX_CONTEXT_MESSAGES:
            return msg_dicts

        # 压缩：前3条 + summary + 后5条
        head = msg_dicts[:COMPRESS_KEEP_HEAD]
        middle = msg_dicts[COMPRESS_KEEP_HEAD:-COMPRESS_KEEP_TAIL]
        tail = msg_dicts[-COMPRESS_KEEP_TAIL:]

        # 生成压缩摘要（简单版：取每条消息的前50字）
        summary_parts = []
        for m in middle:
            short = m["content"][:50].replace("\n", " ")
            summary_parts.append(f"[{m['role']}] {short}...")
        summary = "之前的对话摘要：\n" + "\n".join(summary_parts)

        return head + [{"role": "system", "content": summary}] + tail
