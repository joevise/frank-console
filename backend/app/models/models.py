# -*- coding: utf-8 -*-
"""SQLAlchemy 数据模型。

设计原则：
- 所有业务表都带 user_id，为未来多用户预埋
- 大字段用 JSON/Text，结构化字段单独抽出便于查询
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey, JSON, Integer, Float, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(64), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    watchlists = relationship("WatchlistItem", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    daily_reports = relationship("DailyReport", back_populates="user")
    briefs = relationship("Brief", back_populates="user")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    stock_code = Column(String(16), nullable=False)
    stock_name = Column(String(64), default="")
    mainline = Column(String(64), default="")  # 所属主线
    action = Column(String(16), default="hold")  # hold/watch/buy/sell
    note = Column(Text, default="")  # 用户笔记
    added_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="watchlists")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), default="新对话")
    source = Column(String(16), default="frank")  # frank / dsa / mixed
    openmind_conversation_id = Column(String(128), nullable=True)  # OpenMind conversation_id, for context persistence
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    conversation_id = Column(UUID(as_uuid=False), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # user / assistant / tool
    content = Column(Text, nullable=False)
    source = Column(String(16), default="frank")  # frank / dsa
    tool_calls = Column(JSON, nullable=True)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    conversation = relationship("Conversation", back_populates="messages")


class Brief(Base):
    """每日晨报 — 持久化存储，可回溯。"""
    __tablename__ = "briefs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    brief_date = Column(DateTime, nullable=False, index=True)  # 晨报日期
    content = Column(Text, nullable=False)  # 完整晨报 markdown 内容
    data_sources = Column(JSON, nullable=True)  # DSA 调用了哪些数据源
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="briefs")


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    report_date = Column(DateTime, nullable=False, index=True)
    stock_code = Column(String(16), nullable=False, index=True)
    stock_name = Column(String(64), default="")

    overall_status = Column(String(16), default="neutral")
    signal_score = Column(Float, default=50.0)
    report_data = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="daily_reports")


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=False), ForeignKey("conversations.id"), nullable=True)
    stock_code = Column(String(16), nullable=True, index=True)

    decision_type = Column(String(32), default="advice")
    tools_called = Column(JSON, nullable=True)
    reasoning_summary = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
