#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户黑名单管理API路由（两级黑名单体系 - 用户层）
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
from schemas import (
    BlacklistCreate,
    BlacklistUpdate,
    BlacklistResponse,
    BlacklistListResponse
)
from routers.auth import get_current_user

router = APIRouter(prefix="/api/blacklist", tags=["用户黑名单管理"])


def extract_phone_numbers(text: str) -> List[str]:
    """从文本中提取电话号码"""
    if not text:
        return []
    phone_pattern = re.compile(r'1[3-9]\d{9}')
    phones = phone_pattern.findall(str(text))
    return list(set(phones))


def generate_unique_id() -> str:
    """生成10位唯一标识"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=8))
    return f"BL{random_part}"


@router.post("", response_model=BlacklistResponse, summary="创建用户黑名单条目")
async def create_blacklist(
    blacklist_data: BlacklistCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    创建新的用户黑名单条目
    - 强制设置 owner_id=current_user.id、blacklist_type=USER
    """
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
        # 两级黑名单：强制设置
        owner_id=current_user.id,
        blacklist_type=BlacklistType.USER,
    )

    db.add(blacklist)
    db.commit()
    db.refresh(blacklist)

    return blacklist


@router.get("/statistics", summary="获取当前用户黑名单统计数据")
async def get_blacklist_statistics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    管理员：统计所有用户黑名单
    普通用户：仅统计自己的黑名单，不包含系统黑名单数量
    """
    query = db.query(Blacklist.risk_level, sqlfunc.count(Blacklist.id)).filter(
        Blacklist.blacklist_type == BlacklistType.USER
    )
    if not current_user.is_admin:
        query = query.filter(Blacklist.owner_id == current_user.id)

    rows = query.group_by(Blacklist.risk_level).all()
    counts = {r[0].value if hasattr(r[0], 'value') else r[0]: r[1] for r in rows}
    total = sum(counts.values())
    return {
        "total": total,
        "high": counts.get("HIGH", 0),
        "medium": counts.get("MEDIUM", 0),
        "low": counts.get("LOW", 0),
    }


@router.get("", response_model=BlacklistListResponse, summary="查询用户黑名单列表")
async def get_blacklist_list(
    risk_level: Optional[str] = Query(None, description="风险等级过滤 HIGH/MEDIUM/LOW"),
    search: Optional[str] = Query(None, description="搜索关键词（姓名或电话）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    管理员：查询所有用户的黑名单列表
    普通用户：仅查询自己的黑名单（owner_id=current_user.id AND blacklist_type=USER）
    """
    query = db.query(Blacklist).filter(Blacklist.blacklist_type == BlacklistType.USER)
    if not current_user.is_admin:
        query = query.filter(Blacklist.owner_id == current_user.id)

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


@router.get("/{blacklist_id}", response_model=BlacklistResponse, summary="获取用户黑名单详情")
async def get_blacklist_detail(
    blacklist_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取黑名单条目详情（管理员可查看任意条目，普通用户仅限自己的）"""
    query = db.query(Blacklist).filter(
        Blacklist.id == blacklist_id,
        Blacklist.blacklist_type == BlacklistType.USER
    )
    if not current_user.is_admin:
        query = query.filter(Blacklist.owner_id == current_user.id)
    blacklist = query.first()

    if not blacklist:
        raise HTTPException(status_code=404, detail="黑名单条目不存在")

    return blacklist


@router.put("/{blacklist_id}", response_model=BlacklistResponse, summary="更新用户黑名单条目")
async def update_blacklist(
    blacklist_id: int,
    blacklist_data: BlacklistUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    更新黑名单条目
    - 校验 owner_id == current_user.id，否则返回 403
    """
    blacklist = db.query(Blacklist).filter(Blacklist.id == blacklist_id).first()

    if not blacklist:
        raise HTTPException(status_code=404, detail="黑名单条目不存在")

    if blacklist.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此黑名单条目")

    update_data = blacklist_data.model_dump(exclude_unset=True)

    if 'phone_numbers' in update_data and update_data['phone_numbers']:
        pass
    elif 'order_name_phone' in update_data:
        phone_numbers = extract_phone_numbers(update_data['order_name_phone'])
        update_data['phone_numbers'] = phone_numbers

    if 'risk_level' in update_data:
        update_data['risk_level'] = RiskLevel(update_data['risk_level'])

    # 禁止修改 owner_id 和 blacklist_type
    update_data.pop('owner_id', None)
    update_data.pop('blacklist_type', None)

    for key, value in update_data.items():
        setattr(blacklist, key, value)

    db.commit()
    db.refresh(blacklist)

    return blacklist


@router.delete("/{blacklist_id}", summary="删除用户黑名单条目")
async def delete_blacklist(
    blacklist_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    删除黑名单条目
    - 校验 owner_id == current_user.id，否则返回 403
    """
    blacklist = db.query(Blacklist).filter(Blacklist.id == blacklist_id).first()

    if not blacklist:
        raise HTTPException(status_code=404, detail="黑名单条目不存在")

    if blacklist.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此黑名单条目")

    db.delete(blacklist)
    db.commit()

    return {"success": True, "message": "黑名单条目已删除"}
