#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
站内通知API路由（两级黑名单体系）
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
from models import Notification, User
from routers.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["站内通知"])


# ---- Pydantic schemas ----

class NotificationResponse(BaseModel):
    id: int
    user_id: str
    type: str
    push_request_id: int
    title: str
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    unread_count: int
    items: list[NotificationResponse]


# ---- 路由 ----

@router.get("", response_model=NotificationListResponse, summary="获取通知列表（User）")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """返回当前用户通知列表，按 created_at 倒序，支持分页，响应中包含 unread_count"""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    total = query.count()
    unread_count = query.filter(Notification.is_read == False).count()

    offset = (page - 1) * page_size
    items = query.order_by(Notification.created_at.desc()).offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "unread_count": unread_count,
        "items": items,
    }


@router.get("/unread-count", summary="获取未读通知数量（User）")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """返回当前用户未读通知数量"""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    return {"unread_count": count}


@router.put("/read-all", summary="全部标记已读（User）")
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量将当前用户所有未读通知标记为已读"""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"success": True, "unread_count": 0}


@router.put("/{notification_id}/read", summary="标记单条已读（User）")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记单条通知为已读，返回更新后的未读数量"""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notif:
        raise HTTPException(status_code=404, detail="通知不存在")

    notif.is_read = True
    db.commit()

    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return {"success": True, "unread_count": unread_count}
