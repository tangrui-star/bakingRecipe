#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送申请API路由（两级黑名单体系）
"""

import logging
import uuid
import random
import string
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Blacklist, BlacklistType, RiskLevel,
    PushRequest, PushRequestStatus,
    Notification, NotificationType,
    User
)
from routers.auth import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/push-requests", tags=["推送申请"])


# ---- Pydantic schemas ----

class PushRequestCreate(BaseModel):
    blacklist_id: int
    evidence: str


class RejectBody(BaseModel):
    reject_reason: str


class PushRequestResponse(BaseModel):
    id: int
    blacklist_id: int
    applicant_id: str
    evidence: str
    status: str
    reject_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PushRequestListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PushRequestResponse]


# ---- 辅助函数 ----

def _generate_new_id() -> str:
    chars = string.ascii_uppercase + string.digits
    return "SY" + ''.join(random.choices(chars, k=8))


def _create_notification(
    db: Session,
    user_id: str,
    ntype: NotificationType,
    push_request_id: int,
    title: str,
    content: str
):
    notif = Notification(
        user_id=user_id,
        type=ntype,
        push_request_id=push_request_id,
        title=title,
        content=content,
        is_read=False,
    )
    db.add(notif)


# ---- 路由 ----

@router.post("", response_model=PushRequestResponse, summary="发起推送申请（User）")
async def create_push_request(
    body: PushRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发起推送申请
    - evidence 长度 ≥ 10 字符，否则 400
    - 同一 blacklist_id 已有 PENDING 申请则 409
    """
    if len(body.evidence.strip()) < 10:
        raise HTTPException(status_code=400, detail="证据描述不能少于10个字符")

    # 校验黑名单条目存在且属于当前用户
    entry = db.query(Blacklist).filter(
        Blacklist.id == body.blacklist_id,
        Blacklist.owner_id == current_user.id,
        Blacklist.blacklist_type == BlacklistType.USER
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="黑名单条目不存在或无权操作")

    # 检查是否已有 PENDING 申请
    existing = db.query(PushRequest).filter(
        PushRequest.blacklist_id == body.blacklist_id,
        PushRequest.status == PushRequestStatus.PENDING
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="该条目已有待审核的推送申请")

    pr = PushRequest(
        blacklist_id=body.blacklist_id,
        applicant_id=current_user.id,
        evidence=body.evidence,
        status=PushRequestStatus.PENDING,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)

    return pr


@router.get("/my", response_model=PushRequestListResponse, summary="查询我的推送申请（User）")
async def get_my_push_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """返回当前用户提交的申请列表，含状态和拒绝原因"""
    query = db.query(PushRequest).filter(PushRequest.applicant_id == current_user.id)
    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(PushRequest.created_at.desc()).offset(offset).limit(page_size).all()

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("", response_model=PushRequestListResponse, summary="查询所有推送申请（Admin）")
async def get_all_push_requests(
    status: Optional[str] = Query(None, description="状态过滤 PENDING/APPROVED/REJECTED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """返回所有申请，支持按 status 过滤，分页"""
    query = db.query(PushRequest)
    if status:
        query = query.filter(PushRequest.status == status)
    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(PushRequest.created_at.desc()).offset(offset).limit(page_size).all()

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.post("/{pr_id}/approve", summary="审核通过（Admin）")
async def approve_push_request(
    pr_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    审核通过
    - 校验申请状态为 PENDING，否则 409
    - 将状态更新为 APPROVED
    - 将用户黑名单条目数据复制到系统黑名单，设置 source_push_request_id
    - 触发通知（站内消息 + 邮件）
    """
    pr = db.query(PushRequest).filter(PushRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="推送申请不存在")

    if pr.status != PushRequestStatus.PENDING:
        raise HTTPException(status_code=409, detail="该申请已审核，不可重复操作")

    # 获取原始黑名单条目
    entry = db.query(Blacklist).filter(Blacklist.id == pr.blacklist_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="关联的黑名单条目不存在")

    # 更新申请状态
    pr.status = PushRequestStatus.APPROVED
    pr.reviewed_by = current_user.id
    pr.reviewed_at = datetime.utcnow()

    # 复制到系统黑名单
    new_id = _generate_new_id()
    while db.query(Blacklist).filter(Blacklist.new_id == new_id).first():
        new_id = _generate_new_id()

    system_entry = Blacklist(
        shop_id=entry.shop_id,
        new_id=new_id,
        ktt_name=entry.ktt_name,
        wechat_name=entry.wechat_name,
        wechat_id=entry.wechat_id,
        order_name_phone=entry.order_name_phone,
        phone_numbers=entry.phone_numbers,
        order_address1=entry.order_address1,
        order_address2=entry.order_address2,
        blacklist_reason=entry.blacklist_reason,
        risk_level=entry.risk_level,
        created_by=current_user.id,
        blacklist_type=BlacklistType.SYSTEM,
        owner_id=None,
        source_push_request_id=pr.id,
    )
    db.add(system_entry)

    # 获取申请人信息
    applicant = db.query(User).filter(User.id == pr.applicant_id).first()
    ktt_name = entry.ktt_name or "未知"

    # 创建站内通知
    _create_notification(
        db=db,
        user_id=pr.applicant_id,
        ntype=NotificationType.PUSH_APPROVED,
        push_request_id=pr.id,
        title="推送申请已通过",
        content=f"您提交的黑名单条目「{ktt_name}」推送申请已通过审核，已加入系统黑名单。",
    )

    db.commit()

    # 发送邮件（失败不阻断主流程）
    if applicant and applicant.email:
        try:
            from email_utils import send_push_approved_email
            ok, err = send_push_approved_email(applicant.email, ktt_name)
            if not ok:
                logger.warning(f"审核通过邮件发送失败（不影响主流程）: {err}")
        except Exception as e:
            logger.error(f"审核通过邮件发送异常（不影响主流程）: {e}")

    return {"success": True, "message": "审核通过，已加入系统黑名单"}


@router.post("/{pr_id}/reject", summary="审核拒绝（Admin）")
async def reject_push_request(
    pr_id: int,
    body: RejectBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    审核拒绝
    - 校验申请状态为 PENDING，否则 409
    - 校验 reject_reason 不为空，否则 400
    - 将状态更新为 REJECTED
    - 触发通知（站内消息 + 邮件）
    """
    if not body.reject_reason or not body.reject_reason.strip():
        raise HTTPException(status_code=400, detail="拒绝原因不能为空")

    pr = db.query(PushRequest).filter(PushRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="推送申请不存在")

    if pr.status != PushRequestStatus.PENDING:
        raise HTTPException(status_code=409, detail="该申请已审核，不可重复操作")

    entry = db.query(Blacklist).filter(Blacklist.id == pr.blacklist_id).first()
    ktt_name = entry.ktt_name if entry else "未知"

    # 更新申请状态
    pr.status = PushRequestStatus.REJECTED
    pr.reject_reason = body.reject_reason.strip()
    pr.reviewed_by = current_user.id
    pr.reviewed_at = datetime.utcnow()

    # 获取申请人信息
    applicant = db.query(User).filter(User.id == pr.applicant_id).first()

    # 创建站内通知
    _create_notification(
        db=db,
        user_id=pr.applicant_id,
        ntype=NotificationType.PUSH_REJECTED,
        push_request_id=pr.id,
        title="推送申请未通过",
        content=f"您提交的黑名单条目「{ktt_name}」推送申请未通过审核。拒绝原因：{body.reject_reason.strip()}",
    )

    db.commit()

    # 发送邮件（失败不阻断主流程）
    if applicant and applicant.email:
        try:
            from email_utils import send_push_rejected_email
            ok, err = send_push_rejected_email(applicant.email, ktt_name, body.reject_reason.strip())
            if not ok:
                logger.warning(f"审核拒绝邮件发送失败（不影响主流程）: {err}")
        except Exception as e:
            logger.error(f"审核拒绝邮件发送异常（不影响主流程）: {e}")

    return {"success": True, "message": "审核已拒绝"}
