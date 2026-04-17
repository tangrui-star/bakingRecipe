#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统黑名单管理API路由（两级黑名单体系 - 系统层，Admin Only）
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from typing import Optional, List
import re
import random
import string

from database import get_db
from models import Blacklist, RiskLevel, BlacklistType
from schemas import BlacklistCreate, BlacklistUpdate, BlacklistResponse, BlacklistListResponse
from routers.auth import require_admin

router = APIRouter(prefix="/api/system-blacklist", tags=["系统黑名单管理（Admin）"])


def extract_phone_numbers(text: str) -> List[str]:
    if not text:
        return []
    phone_pattern = re.compile(r'1[3-9]\d{9}')
    phones = phone_pattern.findall(str(text))
    return list(set(phones))


def generate_unique_id() -> str:
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=8))
    return f"SY{random_part}"


@router.post("", response_model=BlacklistResponse, summary="创建系统黑名单条目")
async def create_system_blacklist(
    blacklist_data: BlacklistCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """创建系统黑名单条目，blacklist_type=SYSTEM，owner_id=None"""
    phone_numbers = []
    if blacklist_data.phone_numbers:
        phone_numbers = blacklist_data.phone_numbers
    elif blacklist_data.order_name_phone:
        phone_numbers = extract_phone_numbers(blacklist_data.order_name_phone)

    new_id = generate_unique_id()
    while db.query(Blacklist).filter(Blacklist.new_id == new_id).first():
        new_id = generate_unique_id()

    blacklist = Blacklist(
        shop_id=blacklist_data.shop_id,
        new_id=new_id,
        ktt_name=blacklist_data.ktt_name,
        wechat_name=blacklist_data.wechat_name,
        wechat_id=blacklist_data.wechat_id,
        order_name_phone=blacklist_data.order_name_phone,
        phone_numbers=phone_numbers,
        order_address1=blacklist_data.order_address1,
        order_address2=blacklist_data.order_address2,
        blacklist_reason=blacklist_data.blacklist_reason,
        risk_level=RiskLevel(blacklist_data.risk_level),
        created_by=current_user.id,
        blacklist_type=BlacklistType.SYSTEM,
        owner_id=None,
    )

    db.add(blacklist)
    db.commit()
    db.refresh(blacklist)

    return blacklist


@router.get("/statistics", summary="获取系统黑名单统计数据")
async def get_system_blacklist_statistics(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """返回系统黑名单总数及各风险等级数量"""
    rows = (
        db.query(Blacklist.risk_level, sqlfunc.count(Blacklist.id))
        .filter(Blacklist.blacklist_type == BlacklistType.SYSTEM)
        .group_by(Blacklist.risk_level)
        .all()
    )
    counts = {r[0].value if hasattr(r[0], 'value') else r[0]: r[1] for r in rows}
    total = sum(counts.values())
    return {
        "total": total,
        "high": counts.get("HIGH", 0),
        "medium": counts.get("MEDIUM", 0),
        "low": counts.get("LOW", 0),
    }


@router.get("", response_model=BlacklistListResponse, summary="查询系统黑名单列表")
async def get_system_blacklist_list(
    risk_level: Optional[str] = Query(None, description="风险等级过滤 HIGH/MEDIUM/LOW"),
    search: Optional[str] = Query(None, description="搜索关键词（姓名或电话）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """查询系统黑名单列表，支持分页、风险等级过滤、关键词搜索"""
    query = db.query(Blacklist).filter(Blacklist.blacklist_type == BlacklistType.SYSTEM)

    if risk_level:
        query = query.filter(Blacklist.risk_level == risk_level)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Blacklist.ktt_name.like(search_pattern)) |
            (Blacklist.wechat_name.like(search_pattern)) |
            (Blacklist.order_name_phone.like(search_pattern))
        )

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(Blacklist.created_at.desc()).offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.get("/{blacklist_id}", response_model=BlacklistResponse, summary="获取系统黑名单详情")
async def get_system_blacklist_detail(
    blacklist_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """获取系统黑名单条目详情"""
    blacklist = db.query(Blacklist).filter(
        Blacklist.id == blacklist_id,
        Blacklist.blacklist_type == BlacklistType.SYSTEM
    ).first()

    if not blacklist:
        raise HTTPException(status_code=404, detail="系统黑名单条目不存在")

    return blacklist


@router.put("/{blacklist_id}", response_model=BlacklistResponse, summary="更新系统黑名单条目")
async def update_system_blacklist(
    blacklist_id: int,
    blacklist_data: BlacklistUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """更新系统黑名单条目"""
    blacklist = db.query(Blacklist).filter(
        Blacklist.id == blacklist_id,
        Blacklist.blacklist_type == BlacklistType.SYSTEM
    ).first()

    if not blacklist:
        raise HTTPException(status_code=404, detail="系统黑名单条目不存在")

    update_data = blacklist_data.model_dump(exclude_unset=True)

    if 'phone_numbers' in update_data and update_data['phone_numbers']:
        pass
    elif 'order_name_phone' in update_data:
        update_data['phone_numbers'] = extract_phone_numbers(update_data['order_name_phone'])

    if 'risk_level' in update_data:
        update_data['risk_level'] = RiskLevel(update_data['risk_level'])

    # 禁止修改类型字段
    update_data.pop('owner_id', None)
    update_data.pop('blacklist_type', None)

    for key, value in update_data.items():
        setattr(blacklist, key, value)

    db.commit()
    db.refresh(blacklist)

    return blacklist


@router.delete("/{blacklist_id}", summary="删除系统黑名单条目")
async def delete_system_blacklist(
    blacklist_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """删除系统黑名单条目"""
    blacklist = db.query(Blacklist).filter(
        Blacklist.id == blacklist_id,
        Blacklist.blacklist_type == BlacklistType.SYSTEM
    ).first()

    if not blacklist:
        raise HTTPException(status_code=404, detail="系统黑名单条目不存在")

    db.delete(blacklist)
    db.commit()

    return {"success": True, "message": "系统黑名单条目已删除"}
