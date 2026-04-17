#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单黑名单检查API路由
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any
import pandas as pd
import re
from datetime import datetime
import io

from database import get_db
from models import Blacklist, BlacklistType, OrderScreeningRecord, OrderScreeningDetail
from routers.auth import get_current_user


# 保存检查记录的请求体模型
class SaveScreeningRequest(BaseModel):
    shop_id: str
    file_name: str
    total_orders: int
    matched_count: int
    results: List[Any] = []

router = APIRouter(prefix="/api/screening", tags=["订单检查"])


def extract_phone_from_text(text: str) -> List[str]:
    """从文本中提取电话号码"""
    if not text:
        return []
    phone_pattern = re.compile(r'1[3-9]\d{9}')
    phones = phone_pattern.findall(str(text))
    return list(set(phones))


def find_column(df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
    """
    查找列名（支持多种可能的名称）
    返回第一个匹配的列名，如果都不存在则返回None
    """
    for name in possible_names:
        if name in df.columns:
            return name
    return None


# 列名映射配置
COLUMN_MAPPINGS = {
    'group_no': ['跟团号', '团号', '订单号'],
    'ktt_name': ['下单人', 'KTT名字', 'KTT用户', '用户名'],
    'receiver_name': ['收货人', '姓名', '客户姓名', '收件人'],
    'phone': ['联系电话', '电话', '手机号', '收货电话', '联系方式'],
    'address': ['详细地址', '地址', '收货地址', '收件地址']
}

# 风险等级排序权重
RISK_LEVEL_ORDER = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}


def build_match_reason(match_type: str, match_value: str, blacklist: Blacklist) -> str:
    """生成清晰的匹配原因描述"""
    bl_name = blacklist.ktt_name or blacklist.order_name_phone or '未知'
    reasons = {
        'PHONE':              f'电话号码 {match_value} 与黑名单"{bl_name}"完全一致',
        'NAME_EXACT_ADDRESS': f'下单人/收货人"{match_value}"与黑名单严格一致，且地址高度匹配',
        'NAME_EXACT':         f'下单人/收货人"{match_value}"与黑名单"{bl_name}"严格一致',
    }
    return reasons.get(match_type, f'匹配到黑名单"{bl_name}"')


def address_match_score(addr1: str, addr2: str) -> float:
    """计算两个地址的匹配分数（0~1），按省市区逐级比较"""
    if not addr1 or not addr2:
        return 0.0
    score = 0.0
    for suffix in ['省', '市']:
        idx1, idx2 = addr1.find(suffix), addr2.find(suffix)
        if idx1 > 0 and idx2 > 0 and addr1[:idx1 + 1] == addr2[:idx2 + 1]:
            score += 0.3
            break
    idx1, idx2 = addr1.find('市'), addr2.find('市')
    if idx1 > 0 and idx2 > 0 and addr1[:idx1 + 1] == addr2[:idx2 + 1]:
        score += 0.4
    for suffix in ['区', '县']:
        idx1, idx2 = addr1.find(suffix), addr2.find(suffix)
        if idx1 > 0 and idx2 > 0 and addr1[:idx1 + 1] == addr2[:idx2 + 1]:
            score += 0.3
            break
    return min(score, 1.0)


def blacklist_to_info(bl: Blacklist) -> dict:
    """提取黑名单完整展示信息"""
    return {
        'blacklist_id':          bl.id,
        'blacklist_ktt_name':    bl.ktt_name,
        'blacklist_wechat_name': bl.wechat_name,
        'blacklist_wechat_id':   bl.wechat_id,
        'blacklist_order_name':  bl.order_name_phone,
        'blacklist_phones':      bl.phone_numbers or [],
        'blacklist_address1':    bl.order_address1,
        'blacklist_address2':    bl.order_address2,
        'blacklist_reason':      bl.blacklist_reason,
        'blacklist_risk_level':  bl.risk_level.value if bl.risk_level else None,
    }


def _match_single_list(order_data: dict, blacklist_items: List[Blacklist], source: str) -> Optional[dict]:
    """
    在单个黑名单列表中匹配订单，返回最高风险结果（含 source 字段）。
    匹配规则：
    - HIGH:   电话号码完全一致
    - MEDIUM: 下单人或收货人与黑名单 ktt_name / order_name_phone 严格相等
    """
    ktt_name      = str(order_data.get('ktt_name', '')).strip()
    receiver_name = str(order_data.get('receiver_name', '')).strip()
    order_phones  = extract_phone_from_text(order_data.get('phone', ''))
    order_address = str(order_data.get('address', '')).strip()

    best = None  # {'priority': int, 'result': dict}

    for bl in blacklist_items:
        bl_ktt   = (bl.ktt_name or '').strip()
        bl_order = (bl.order_name_phone or '').strip()

        # ── 1. 电话号码完全一致 → HIGH（直接返回，最高优先级）──────
        if bl.phone_numbers and order_phones:
            for phone in order_phones:
                if phone in bl.phone_numbers:
                    result = {
                        'match_type':    'PHONE',
                        'match_value':   phone,
                        'match_reason':  build_match_reason('PHONE', phone, bl),
                        'risk_level':    'HIGH',
                        'confidence':    100,
                        'source':        source,
                        **blacklist_to_info(bl),
                    }
                    return result

        # ── 2. 名字严格相等 → MEDIUM ────────────────────────────────
        matched_name = ''
        for order_name in filter(None, [ktt_name, receiver_name]):
            if (bl_ktt and order_name == bl_ktt) or \
               (bl_order and order_name == bl_order):
                matched_name = order_name
                break

        if matched_name:
            bl_addr = bl.order_address1 or bl.order_address2 or ''
            addr_score = address_match_score(order_address, bl_addr) if order_address and bl_addr else 0.0
            match_type = 'NAME_EXACT_ADDRESS' if addr_score >= 0.4 else 'NAME_EXACT'
            result = {
                'match_type':    match_type,
                'match_value':   matched_name,
                'match_reason':  build_match_reason(match_type, matched_name, bl),
                'risk_level':    'MEDIUM',
                'confidence':    85 if addr_score >= 0.4 else 70,
                'source':        source,
                **blacklist_to_info(bl),
            }
            if best is None or best['priority'] > 1:
                best = {'priority': 1, 'result': result}

    return best['result'] if best else None


def match_blacklist(order_data: dict, system_items: List[Blacklist], user_items: List[Blacklist]) -> Optional[dict]:
    """
    双库匹配：分别在系统黑名单和用户黑名单中匹配，合并结果。
    同一订单同时命中两库时，取风险等级更高的结果（HIGH > MEDIUM > LOW），
    source 字段标注实际来源。
    """
    system_result = _match_single_list(order_data, system_items, 'SYSTEM')
    user_result   = _match_single_list(order_data, user_items, 'USER')

    if system_result is None:
        return user_result
    if user_result is None:
        return system_result

    # 两库都命中，取风险等级更高的
    sys_priority  = RISK_LEVEL_ORDER.get(system_result.get('risk_level', 'LOW'), 2)
    user_priority = RISK_LEVEL_ORDER.get(user_result.get('risk_level', 'LOW'), 2)
    # 数值越小优先级越高（HIGH=0, MEDIUM=1, LOW=2）
    return system_result if sys_priority <= user_priority else user_result


@router.post("/check-orders", summary="检查订单Excel文件")
async def check_orders(
    file: UploadFile = File(...),
    shop_id: str = Query(..., description="店铺ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """上传订单Excel文件并检查黑名单，结果按风险等级排序"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        # 自动识别列名
        group_no_col     = find_column(df, COLUMN_MAPPINGS['group_no'])
        ktt_name_col     = find_column(df, COLUMN_MAPPINGS['ktt_name'])
        receiver_name_col = find_column(df, COLUMN_MAPPINGS['receiver_name'])
        phone_col        = find_column(df, COLUMN_MAPPINGS['phone'])
        address_col      = find_column(df, COLUMN_MAPPINGS['address'])

        # 至少需要收货人和电话
        if not receiver_name_col or not phone_col:
            missing = []
            if not receiver_name_col:
                missing.append('收货人/姓名')
            if not phone_col:
                missing.append('联系电话/电话')
            raise HTTPException(status_code=400, detail=f"Excel文件缺少必要的列: {', '.join(missing)}")

        system_items = db.query(Blacklist).filter(
            Blacklist.blacklist_type == BlacklistType.SYSTEM
        ).all()
        user_items = db.query(Blacklist).filter(
            Blacklist.blacklist_type == BlacklistType.USER,
            Blacklist.owner_id == current_user.id
        ).all()

        if not system_items and not user_items:
            return {
                'file_name': file.filename,
                'total_orders': len(df),
                'matched_count': 0,
                'results': [],
                'message': '黑名单为空，无法进行检查'
            }

        results = []
        for index, row in df.iterrows():
            def get_val(col):
                if not col:
                    return ''
                v = row.get(col, '')
                return '' if pd.isna(v) else str(v).strip()

            order_data = {
                'group_no':      get_val(group_no_col),
                'ktt_name':      get_val(ktt_name_col),
                'receiver_name': get_val(receiver_name_col),
                'phone':         get_val(phone_col),
                'address':       get_val(address_col),
                'row_number':    index + 2
            }

            match_result = match_blacklist(order_data, system_items, user_items)
            if match_result:
                results.append({
                    'row_number':    order_data['row_number'],
                    'group_no':      order_data['group_no'],
                    'ktt_name':      order_data['ktt_name'],
                    'order_name':    order_data['receiver_name'],
                    'order_phone':   order_data['phone'],
                    'order_address': order_data['address'],
                    **match_result
                })

        # 按风险等级排序：HIGH → MEDIUM → LOW
        results.sort(key=lambda x: RISK_LEVEL_ORDER.get(x.get('risk_level', 'LOW'), 2))

        return {
            'file_name': file.filename,
            'total_orders': len(df),
            'matched_count': len(results),
            'results': results,
            'column_mapping': {
                'group_no': group_no_col,
                'ktt_name': ktt_name_col,
                'receiver_name': receiver_name_col,
                'phone': phone_col,
                'address': address_col
            }
        }

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Excel文件为空")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理文件时出错: {str(e)}")


@router.post("/save-screening", summary="保存检查记录")
async def save_screening(
    screening_data: SaveScreeningRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """保存订单检查记录到数据库（幂等：同文件5分钟内不重复保存）"""
    from datetime import timedelta

    # ── 幂等检查：同 shop + 文件名 + 订单数 + 命中数，5分钟内已存在则直接返回 ──
    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    existing = db.query(OrderScreeningRecord).filter(
        OrderScreeningRecord.shop_id    == screening_data.shop_id,
        OrderScreeningRecord.file_name  == screening_data.file_name,
        OrderScreeningRecord.total_orders  == screening_data.total_orders,
        OrderScreeningRecord.matched_count == screening_data.matched_count,
        OrderScreeningRecord.created_by == current_user.id,
        OrderScreeningRecord.created_at >= five_min_ago,
    ).first()

    if existing:
        return {
            'success': True,
            'screening_id': existing.id,
            'message': '检查记录已存在，无需重复保存'
        }

    try:
        record = OrderScreeningRecord(
            shop_id=screening_data.shop_id,
            file_name=screening_data.file_name,
            total_orders=screening_data.total_orders,
            matched_count=screening_data.matched_count,
            created_by=current_user.id
        )
        db.add(record)
        db.flush()

        for result in screening_data.results:
            detail = OrderScreeningDetail(
                screening_id=record.id,
                order_name=result.get('order_name'),
                order_phone=result.get('order_phone'),
                order_address=result.get('order_address'),
                order_data=result,
                blacklist_id=result['blacklist_id'],
                match_type=result['match_type'],
                match_value=result.get('match_value'),
                risk_level=result['risk_level']
            )
            db.add(detail)

        db.commit()
        db.refresh(record)

        return {
            'success': True,
            'screening_id': record.id,
            'message': '检查记录保存成功'
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/history", summary="获取检查历史列表")
async def get_screening_history(
    shop_id: str = Query(..., description="店铺ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取订单检查历史记录列表"""
    query = db.query(OrderScreeningRecord).filter(
        OrderScreeningRecord.shop_id == shop_id
    )
    
    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(OrderScreeningRecord.screening_time.desc()).offset(offset).limit(page_size).all()
    
    return {
        'total': total,
        'page': page,
        'page_size': page_size,
        'items': [
            {
                'id': item.id,
                'file_name': item.file_name,
                'total_orders': item.total_orders,
                'matched_count': item.matched_count,
                'screening_time': item.screening_time.isoformat(),
                'created_at': item.created_at.isoformat()
            }
            for item in items
        ]
    }


@router.get("/history/{screening_id}", summary="获取检查详情")
async def get_screening_detail(
    screening_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取订单检查详情，按风险等级排序"""
    record = db.query(OrderScreeningRecord).filter(
        OrderScreeningRecord.id == screening_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="检查记录不存在")

    details = db.query(OrderScreeningDetail).filter(
        OrderScreeningDetail.screening_id == screening_id
    ).all()

    # 按风险等级排序
    def risk_sort(d):
        return RISK_LEVEL_ORDER.get(d.risk_level, 2)

    details_sorted = sorted(details, key=risk_sort)

    return {
        'id': record.id,
        'file_name': record.file_name,
        'total_orders': record.total_orders,
        'matched_count': record.matched_count,
        'screening_time': record.screening_time.isoformat(),
        'details': [
            {
                'id': detail.id,
                # 订单信息
                'group_no':      detail.order_data.get('group_no', '') if detail.order_data else '',
                'ktt_name':      detail.order_data.get('ktt_name', '') if detail.order_data else '',
                'order_name':    detail.order_name,
                'order_phone':   detail.order_phone,
                'order_address': detail.order_address,
                # 匹配信息
                'match_type':    detail.match_type,
                'match_value':   detail.match_value,
                'match_reason':  detail.order_data.get('match_reason', '') if detail.order_data else '',
                'confidence':    detail.order_data.get('confidence', 0) if detail.order_data else 0,
                'risk_level':    detail.risk_level,
                # 黑名单完整信息
                'blacklist_id':          detail.blacklist_id,
                'blacklist_ktt_name':    detail.order_data.get('blacklist_ktt_name') if detail.order_data else (detail.blacklist.ktt_name if detail.blacklist else None),
                'blacklist_wechat_name': detail.order_data.get('blacklist_wechat_name') if detail.order_data else None,
                'blacklist_wechat_id':   detail.order_data.get('blacklist_wechat_id') if detail.order_data else None,
                'blacklist_order_name':  detail.order_data.get('blacklist_order_name') if detail.order_data else None,
                'blacklist_phones':      detail.order_data.get('blacklist_phones', []) if detail.order_data else [],
                'blacklist_address1':    detail.order_data.get('blacklist_address1') if detail.order_data else None,
                'blacklist_address2':    detail.order_data.get('blacklist_address2') if detail.order_data else None,
                'blacklist_reason':      detail.order_data.get('blacklist_reason') if detail.order_data else (detail.blacklist.blacklist_reason if detail.blacklist else None),
            }
            for detail in details_sorted
        ]
    }


@router.delete("/history/{screening_id}", summary="删除检查记录")
async def delete_screening(
    screening_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除订单检查记录"""
    record = db.query(OrderScreeningRecord).filter(
        OrderScreeningRecord.id == screening_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="检查记录不存在")
    
    db.delete(record)
    db.commit()
    
    return {'success': True, 'message': '检查记录已删除'}
