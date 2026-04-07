#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单数据处理记录 API
（计算逻辑在前端完成，后端只负责保存和查询处理记录）
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Any, Optional
from datetime import datetime

from database import get_db
from models import OrderProcessRecord
from routers.auth import get_current_user

router = APIRouter(prefix="/api/order-process", tags=["订单数据处理"])


class SaveProcessRequest(BaseModel):
    shop_id: str
    file_name: str
    group_nos: List[int]
    total_orders: int
    product_types: int
    summary: Optional[List[Any]] = []


@router.post("/save", summary="保存处理记录")
async def save_process_record(
    data: SaveProcessRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """保存一次订单数据处理的元数据记录（幂等：同文件+跟团号组合5分钟内不重复）"""
    from datetime import timedelta

    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    existing = db.query(OrderProcessRecord).filter(
        OrderProcessRecord.shop_id == data.shop_id,
        OrderProcessRecord.file_name == data.file_name,
        OrderProcessRecord.total_orders == data.total_orders,
        OrderProcessRecord.created_by == current_user.id,
        OrderProcessRecord.created_at >= five_min_ago,
    ).first()

    if existing:
        return {'success': True, 'record_id': existing.id, 'message': '记录已存在'}

    record = OrderProcessRecord(
        shop_id=data.shop_id,
        file_name=data.file_name,
        group_nos=data.group_nos,
        total_orders=data.total_orders,
        product_types=data.product_types,
        summary=data.summary[:10] if data.summary else [],
        created_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {'success': True, 'record_id': record.id, 'message': '保存成功'}


@router.get("/history", summary="获取处理历史列表")
async def get_history(
    shop_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(OrderProcessRecord).filter(OrderProcessRecord.shop_id == shop_id)
    total = query.count()
    items = query.order_by(OrderProcessRecord.created_at.desc()) \
                 .offset((page - 1) * page_size).limit(page_size).all()
    return {
        'total': total,
        'page': page,
        'page_size': page_size,
        'items': [
            {
                'id': r.id,
                'file_name': r.file_name,
                'group_nos': r.group_nos,
                'total_orders': r.total_orders,
                'product_types': r.product_types,
                'summary': r.summary,
                'created_at': r.created_at.isoformat(),
            }
            for r in items
        ]
    }


@router.delete("/history/{record_id}", summary="删除处理记录")
async def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    record = db.query(OrderProcessRecord).filter(OrderProcessRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {'success': True}
