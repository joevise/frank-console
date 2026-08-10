# -*- coding: utf-8 -*-
"""自选股 API — 完整 CRUD。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models.models import WatchlistItem, User
from app.api.market import fetch_quotes_for_codes, compute_health, get_bull_industry_names

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


class AddStockRequest(BaseModel):
    stock_code: str
    stock_name: Optional[str] = ""
    mainline: Optional[str] = ""
    action: Optional[str] = "hold"
    note: Optional[str] = ""


class UpdateStockRequest(BaseModel):
    stock_name: Optional[str] = None
    mainline: Optional[str] = None
    action: Optional[str] = None
    note: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.is_active == True,
    ).order_by(WatchlistItem.added_at.desc()).all()

    codes = [it.stock_code for it in items]
    quotes = fetch_quotes_for_codes(codes)
    bull_names = get_bull_industry_names()

    result = []
    for it in items:
        quote = quotes.get(it.stock_code)
        in_mainline = bool(it.mainline and it.mainline in bull_names)
        health = compute_health(quote, in_mainline)
        # Fill stock_name from live quote if missing
        name = it.stock_name or (quote.get("name") if quote else "") or it.stock_code
        result.append({
            "id": it.id,
            "stock_code": it.stock_code,
            "stock_name": name,
            "mainline": it.mainline,
            "action": it.action,
            "note": it.note,
            "added_at": it.added_at.isoformat(),
            "quote": quote,
            "health_score": health["score"],
            "health_status": health["status"],
            "health_factors": health["factors"],
        })
    return result


@router.post("")
def add_stock(
    req: AddStockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 检查是否已存在
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.stock_code == req.stock_code,
        WatchlistItem.is_active == True,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该股票已在自选列表中")

    item = WatchlistItem(
        user_id=current_user.id,
        stock_code=req.stock_code,
        stock_name=req.stock_name,
        mainline=req.mainline,
        action=req.action,
        note=req.note,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "stock_code": item.stock_code,
        "stock_name": item.stock_name,
        "mainline": item.mainline,
        "action": item.action,
    }


@router.put("/{item_id}")
def update_stock(
    item_id: str,
    req: UpdateStockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(WatchlistItem).filter(
        WatchlistItem.id == item_id,
        WatchlistItem.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="自选股不存在")

    if req.stock_name is not None:
        item.stock_name = req.stock_name
    if req.mainline is not None:
        item.mainline = req.mainline
    if req.action is not None:
        item.action = req.action
    if req.note is not None:
        item.note = req.note
    if req.is_active is not None:
        item.is_active = req.is_active

    db.commit()
    db.refresh(item)
    return {"id": item.id, "stock_code": item.stock_code, "updated": True}


@router.delete("/{item_id}")
def remove_stock(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(WatchlistItem).filter(
        WatchlistItem.id == item_id,
        WatchlistItem.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="自选股不存在")

    item.is_active = False
    db.commit()
    return {"removed": True}
