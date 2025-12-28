from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List
from decimal import Decimal
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
    
    # 检查用户是否有会员卡
    if not user.member_card:
        raise HTTPException(status_code=400, detail="该用户未开通会员卡，无法调整积分")
    
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


@router.post("/payments/{payment_id}/earn", response_model=PointRecordResponse, summary="支付获得积分")
async def earn_points_from_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根据支付记录自动计算并发放积分
    - 规则：1元 = 1积分
    - 仅已支付(paid)状态的支付记录可发放积分
    """
    from app.models.payment import Payment, PaymentStatus
    
    # 查询支付记录
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")
    
    # 检查支付状态
    if payment.status != PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="仅已支付状态的记录可发放积分")
    
    # 权限检查
    if current_user.role != "admin" and current_user.id != payment.user_id:
        raise HTTPException(status_code=403, detail="无权操作")
    
    # 检查是否已经发放积分（使用 payment_id 作为 related_id）
    existing_record = db.query(PointRecord).filter(
        PointRecord.user_id == payment.user_id,
        PointRecord.type == PointRecordType.EARN,
        PointRecord.reason.like(f"%支付#{payment_id}%")
    ).first()
    if existing_record:
        raise HTTPException(status_code=400, detail="该支付已发放积分")
    
    # 计算积分 (1元 = 1积分)
    points = int(payment.amount) if payment.amount else 0
    if points <= 0:
        raise HTTPException(status_code=400, detail="支付金额无效")
    
    # 获取用户
    user = db.query(User).filter(User.id == payment.user_id).first()
    
    # 更新用户积分
    user.points += points
    user.total_points += points
    
    # 创建积分记录
    point_record = PointRecord(
        user_id=payment.user_id,
        points=points,
        balance=user.points,
        type=PointRecordType.EARN,
        reason=f"支付#{payment_id}获得积分"
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


@router.get("/me/stats", summary="获取我的积分统计")
async def get_my_point_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的积分统计信息
    包括：当前积分、累计获得、累计使用
    """
    # 计算已使用积分（绝对值）
    used_points = db.query(func.sum(PointRecord.points)).filter(
        PointRecord.user_id == current_user.id,
        PointRecord.type == PointRecordType.USE
    ).scalar() or 0
    
    # 计算累计获得积分
    earned_points = db.query(func.sum(PointRecord.points)).filter(
        PointRecord.user_id == current_user.id,
        PointRecord.type == PointRecordType.EARN
    ).scalar() or 0
    
    return {
        "current_points": current_user.points,
        "total_earned": abs(earned_points),
        "total_used": abs(used_points)
    }


@router.get("/me/records", response_model=List[PointRecordResponse], summary="获取我的积分明细")
async def get_my_point_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的积分明细记录"""
    records = db.query(PointRecord).filter(
        PointRecord.user_id == current_user.id
    ).order_by(desc(PointRecord.created_at)).offset(skip).limit(limit).all()
    
    return records


@router.post("/use", summary="使用积分抵扣订单")
async def use_points_for_discount(
    order_id: int,
    points: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    使用积分抵扣订单金额
    规则：100积分=1元，100积分起用
    """
    # 验证积分数量
    if points < 100 or points % 100 != 0:
        raise HTTPException(status_code=400, detail="积分必须是100的倍数且不少于100")
    
    # 检查用户积分是否足够
    if current_user.points < points:
        raise HTTPException(status_code=400, detail="积分不足")
    
    # 计算抵扣金额
    discount_amount = Decimal(points) / 100
    
    # 扣除积分
    current_user.points -= points
    
    # 创建积分使用记录
    point_record = PointRecord(
        user_id=current_user.id,
        points=-points,
        balance=current_user.points,
        type=PointRecordType.USE,
        reason=f"订单#{order_id}积分抵扣"
    )
    db.add(point_record)
    db.commit()
    db.refresh(point_record)
    
    return {
        "success": True,
        "points_used": points,
        "discount_amount": float(discount_amount),
        "remaining_points": current_user.points
    }


@router.get("/calculate", summary="计算积分可抵扣金额")
async def calculate_points_value(
    points: int = Query(..., ge=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """计算指定积分可以抵扣的金额"""
    # 验证积分数量
    if points % 100 != 0:
        raise HTTPException(status_code=400, detail="积分必须是100的倍数")
    
    if points > current_user.points:
        raise HTTPException(status_code=400, detail="积分不足")
    
    value = Decimal(points) / 100
    
    return {
        "points": points,
        "value": float(value)
    }
