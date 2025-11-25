from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from app.database import get_db
from app.models.member import PointRecord, PointRecordType
from app.models.user import User
from app.schemas.member import (
    PointRecordResponse,
    PointAdjust
)
from app.utils.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/points", tags=["积分管理"])


@router.get("/users/{user_id}/records", response_model=List[PointRecordResponse], summary="获取用户积分明细")
async def get_user_point_records(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定用户的积分明细记录
    - 普通用户只能查看自己的记录
    - 管理员可以查看所有用户的记录
    """
    # 权限检查
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="无权查看其他用户的积分记录")
    
    # 查询积分记录
    records = db.query(PointRecord).filter(
        PointRecord.user_id == user_id
    ).order_by(desc(PointRecord.created_at)).offset(skip).limit(limit).all()
    
    return records


@router.post("/users/{user_id}/adjust", response_model=PointRecordResponse, summary="手动调整用户积分")
async def adjust_user_points(
    user_id: int,
    adjust: PointAdjust,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    手动调整用户积分
    - 仅管理员可操作
    - 可以增加或减少积分
    """
    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 计算新积分
    new_points = user.points + adjust.points
    if new_points < 0:
        raise HTTPException(status_code=400, detail="积分不足，无法扣减")
    
    # 更新用户积分
    user.points = new_points
    if adjust.points > 0:
        user.total_points += adjust.points
    
    # 创建积分记录
    point_record = PointRecord(
        user_id=user_id,
        points=adjust.points,
        balance=user.points,
        type=PointRecordType.ADJUST,
        reason=adjust.reason,
        operator_id=current_user.id
    )
    db.add(point_record)
    
    # 检查会员等级升级
    _check_and_upgrade_level(user, db)
    
    db.commit()
    db.refresh(point_record)
    
    return point_record


@router.post("/transactions/{transaction_id}/earn", response_model=PointRecordResponse, summary="消费获得积分")
async def earn_points_from_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根据交易自动计算并发放积分
    - 规则：1元 = 1积分
    """
    from app.models.transaction import Transaction
    from decimal import Decimal
    
    # 查询交易
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="交易不存在")
    
    # 权限检查
    if current_user.role != "admin" and current_user.id != transaction.user_id:
        raise HTTPException(status_code=403, detail="无权操作")
    
    # 检查是否已经发放积分
    existing_record = db.query(PointRecord).filter(
        PointRecord.transaction_id == transaction_id,
        PointRecord.type == PointRecordType.EARN
    ).first()
    if existing_record:
        raise HTTPException(status_code=400, detail="该交易已发放积分")
    
    # 计算积分 (1元 = 1积分)
    points = int(transaction.amount) if transaction.amount else 0
    if points <= 0:
        raise HTTPException(status_code=400, detail="交易金额无效")
    
    # 获取用户
    user = db.query(User).filter(User.id == transaction.user_id).first()
    
    # 更新用户积分
    user.points += points
    user.total_points += points
    
    # 创建积分记录
    point_record = PointRecord(
        user_id=transaction.user_id,
        points=points,
        balance=user.points,
        type=PointRecordType.EARN,
        reason=f"消费获得积分",
        transaction_id=transaction_id
    )
    db.add(point_record)
    
    # 检查会员等级升级
    _check_and_upgrade_level(user, db)
    
    db.commit()
    db.refresh(point_record)
    
    return point_record


def _check_and_upgrade_level(user: User, db: Session):
    """检查并自动升级用户会员等级"""
    from app.models.member import MemberLevel
    
    # 获取所有等级，按level降序
    levels = db.query(MemberLevel).filter(
        MemberLevel.is_active == True
    ).order_by(desc(MemberLevel.level)).all()
    
    # 找到用户应该对应的等级
    for level in levels:
        if user.total_points >= level.min_points:
            if user.member_level_id != level.id:
                user.member_level_id = level.id
            break
