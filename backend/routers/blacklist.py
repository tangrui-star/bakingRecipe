#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黑名单管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import re
import random
import string

from database import get_db
from models import Blacklist, RiskLevel
from schemas import (
    BlacklistCreate,
    BlacklistUpdate,
    BlacklistResponse,
    BlacklistListResponse
)
from routers.auth import get_current_user

router = APIRouter(prefix="/api/blacklist", tags=["黑名单管理"])


def extract_phone_numbers(text: str) -> List[str]:
    """从文本中提取电话号码"""
    if not text:
        return []
    # 中国手机号正则：1[3-9]\d{9}
    phone_pattern = re.compile(r'1[3-9]\d{9}')
    phones = phone_pattern.findall(str(text))
    return list(set(phones))  # 去重


def generate_unique_id() -> str:
    """生成10位唯一标识"""
    # 生成格式：BL + 8位随机字符（数字+大写字母）
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=8))
    return f"BL{random_part}"


@router.post("", response_model=BlacklistResponse, summary="创建黑名单条目")
async def create_blacklist(
    blacklist_data: BlacklistCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    创建新的黑名单条目
    
    - 支持直接传入phone_numbers数组或从order_name_phone提取
    - 生成唯一标识
    - 记录创建人
    """
    # 获取电话号码列表
    phone_numbers = []
    if blacklist_data.phone_numbers:
        # 如果直接提供了phone_numbers数组，使用它
        phone_numbers = blacklist_data.phone_numbers
    elif blacklist_data.order_name_phone:
        # 否则从order_name_phone提取
        phone_numbers = extract_phone_numbers(blacklist_data.order_name_phone)
    
    # 生成唯一标识
    new_id = generate_unique_id()
    while db.query(Blacklist).filter(Blacklist.new_id == new_id).first():
        new_id = generate_unique_id()
    
    # 创建黑名单条目
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
        created_by=current_user.id
    )
    
    db.add(blacklist)
    db.commit()
    db.refresh(blacklist)
    
    return blacklist


@router.get("", response_model=BlacklistListResponse, summary="查询黑名单列表")
async def get_blacklist_list(
    shop_id: str = Query(..., description="店铺ID"),
    risk_level: Optional[str] = Query(None, description="风险等级过滤"),
    search: Optional[str] = Query(None, description="搜索关键词（姓名或电话）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    查询黑名单列表
    
    - 支持按风险等级过滤
    - 支持按姓名或电话搜索
    - 支持分页
    """
    # 构建查询
    query = db.query(Blacklist).filter(Blacklist.shop_id == shop_id)
    
    # 风险等级过滤
    if risk_level:
        query = query.filter(Blacklist.risk_level == risk_level)
    
    # 搜索过滤
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Blacklist.ktt_name.like(search_pattern)) |
            (Blacklist.wechat_name.like(search_pattern)) |
            (Blacklist.order_name_phone.like(search_pattern))
        )
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    items = query.order_by(Blacklist.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items
    }


@router.get("/{blacklist_id}", response_model=BlacklistResponse, summary="获取黑名单详情")
async def get_blacklist_detail(
    blacklist_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取黑名单条目详情"""
    blacklist = db.query(Blacklist).filter(Blacklist.id == blacklist_id).first()
    
    if not blacklist:
        raise HTTPException(status_code=404, detail="黑名单条目不存在")
    
    return blacklist


@router.put("/{blacklist_id}", response_model=BlacklistResponse, summary="更新黑名单条目")
async def update_blacklist(
    blacklist_id: int,
    blacklist_data: BlacklistUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    更新黑名单条目
    
    - 支持直接传入phone_numbers数组或从order_name_phone提取
    """
    blacklist = db.query(Blacklist).filter(Blacklist.id == blacklist_id).first()
    
    if not blacklist:
        raise HTTPException(status_code=404, detail="黑名单条目不存在")
    
    # 更新字段
    update_data = blacklist_data.model_dump(exclude_unset=True)
    
    # 处理电话号码
    if 'phone_numbers' in update_data and update_data['phone_numbers']:
        # 如果直接提供了phone_numbers数组，使用它
        pass  # 保持原样
    elif 'order_name_phone' in update_data:
        # 如果更新了order_name_phone但没有phone_numbers，从中提取
        phone_numbers = extract_phone_numbers(update_data['order_name_phone'])
        update_data['phone_numbers'] = phone_numbers
    
    # 如果更新了risk_level，转换为枚举
    if 'risk_level' in update_data:
        update_data['risk_level'] = RiskLevel(update_data['risk_level'])
    
    for key, value in update_data.items():
        setattr(blacklist, key, value)
    
    db.commit()
    db.refresh(blacklist)
    
    return blacklist


@router.delete("/{blacklist_id}", summary="删除黑名单条目")
async def delete_blacklist(
    blacklist_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除黑名单条目"""
    blacklist = db.query(Blacklist).filter(Blacklist.id == blacklist_id).first()
    
    if not blacklist:
        raise HTTPException(status_code=404, detail="黑名单条目不存在")
    
    db.delete(blacklist)
    db.commit()
    
    return {"success": True, "message": "黑名单条目已删除"}
