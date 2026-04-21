#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员后台API路由（两级黑名单体系）
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from typing import Optional
from datetime import datetime

from database import get_db
from models import Blacklist, BlacklistType, PushRequest, PushRequestStatus, User
from routers.auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["管理员后台"])


# ---- Pydantic schemas ----

class UserAdminResponse(BaseModel):
    id: str
    username: str
    email: str
    phone: Optional[str] = None
    is_active: bool
    is_admin: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserAdminResponse]


# ---- 路由 ----

@router.get("/statistics", summary="获取管理员统计数据")
async def get_admin_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """返回系统黑名单、用户黑名单各风险等级数量、待审核 Push_Request 数量"""
    # 系统黑名单统计
    sys_rows = (
        db.query(Blacklist.risk_level, sqlfunc.count(Blacklist.id))
        .filter(Blacklist.blacklist_type == BlacklistType.SYSTEM)
        .group_by(Blacklist.risk_level)
        .all()
    )
    sys_counts = {r[0].value if hasattr(r[0], 'value') else r[0]: r[1] for r in sys_rows}

    # 用户黑名单统计（所有用户）
    user_rows = (
        db.query(Blacklist.risk_level, sqlfunc.count(Blacklist.id))
        .filter(Blacklist.blacklist_type == BlacklistType.USER)
        .group_by(Blacklist.risk_level)
        .all()
    )
    user_counts = {r[0].value if hasattr(r[0], 'value') else r[0]: r[1] for r in user_rows}

    pending_count = db.query(PushRequest).filter(
        PushRequest.status == PushRequestStatus.PENDING
    ).count()

    return {
        # 系统黑名单
        "system_blacklist_total": sum(sys_counts.values()),
        "system_blacklist_high": sys_counts.get("HIGH", 0),
        "system_blacklist_medium": sys_counts.get("MEDIUM", 0),
        "system_blacklist_low": sys_counts.get("LOW", 0),
        # 用户黑名单（全平台）
        "user_blacklist_total": sum(user_counts.values()),
        "user_blacklist_high": user_counts.get("HIGH", 0),
        "user_blacklist_medium": user_counts.get("MEDIUM", 0),
        "user_blacklist_low": user_counts.get("LOW", 0),
        # 待审核
        "pending_push_requests": pending_count,
    }


@router.get("/users", response_model=UserListResponse, summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """返回用户列表（分页）"""
    query = db.query(User)
    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.put("/users/{user_id}/toggle-active", summary="启用/禁用用户")
async def toggle_user_active(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """启用或禁用指定用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    status_text = "启用" if user.is_active else "禁用"
    return {"success": True, "message": f"用户已{status_text}", "is_active": user.is_active}
