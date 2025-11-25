from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from app.database import get_db
from app.models.member import MemberCard, CardRechargeRecord
from app.models.user import User
from app.schemas.member import (
    MemberCardCreate,
   MemberCardResponse,
    CardRechargeRequest,
    CardRechargeRecordResponse
)
from app.utils.dependencies import get_current_user, require_admin
import random
import string

router = APIRouter(prefix="/member_cards", tags=["会员卡"])


def generate_card_number() -> str:
    """生成会员卡号"""
    return "".join(random.choices(string.digits, k=16))


@router.post("/", response_model=MemberCardResponse, summary="开通会员卡")
async def create_member_card(
    card_in: MemberCardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    为用户开通会员卡
    - 仅管理员可操作
    - 自动生成唯一卡号
    """
    # 检查用户是否存在
    user = db.query(User).filter(User.id == card_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查用户是否已有会员卡
    existing_card = db.query(MemberCard).filter(MemberCard.user_id == card_in.user_id).first()
    if existing_card:
        raise HTTPException(status_code=400, detail="用户已有会员卡")
    
    # 生成唯一卡号
    while True:
        card_number = generate_card_number()
        if not db.query(MemberCard).filter(MemberCard.card_number == card_number).first():
            break
    
    # 创建会员卡
    member_card = MemberCard(
        user_id=card_in.user_id,
        card_number=card_number
    )
    db.add(member_card)
    db.commit()
    db.refresh(member_card)
    
    return member_card


@router.get("/{card_id}", response_model=MemberCardResponse, summary="查询会员卡详情")
async def get_member_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询会员卡详情
    - 普通用户只能查询自己的卡
    - 管理员可以查询所有卡
    """
    card = db.query(MemberCard).filter(MemberCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="会员卡不存在")
    
    # 权限检查
    if current_user.role != "admin" and card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此会员卡")
    
    return card


@router.get("/users/{user_id}", response_model=MemberCardResponse, summary="查询用户的会员卡")
async def get_user_member_card(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询指定用户的会员卡
    - 普通用户只能查询自己的卡
    - 管理员可以查询所有用户的卡
    """
    # 权限检查
    if current_user.role != "admin" and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此用户的会员卡")
    
    card = db.query(MemberCard).filter(MemberCard.user_id == user_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="该用户暂无会员卡")
    
    return card


@router.post("/{card_id}/recharge", response_model=CardRechargeRecordResponse, summary="会员卡充值")
async def recharge_member_card(
    card_id: int,
    recharge: CardRechargeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    会员卡充值
    - 仅管理员可操作
    - 记录充值明细
    """
    # 查询会员卡
    card = db.query(MemberCard).filter(MemberCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="会员卡不存在")
    
    if card.status != "active":
        raise HTTPException(status_code=400, detail="会员卡状态异常，无法充值")
    
    # 记录充值前余额
    balance_before = card.balance
    balance_after = balance_before + recharge.amount
    
    # 更新会员卡余额
    card.balance = balance_after
    card.total_recharge += recharge.amount
    
    # 创建充值记录
    recharge_record = CardRechargeRecord(
        member_card_id=card_id,
        amount=recharge.amount,
        balance_before=balance_before,
        balance_after=balance_after,
        payment_method=recharge.payment_method,
        operator_id=current_user.id,
        remark= recharge.remark
    )
    db.add(recharge_record)
    
    db.commit()
    db.refresh(recharge_record)
    
    return recharge_record


@router.get("/{card_id}/recharge_records", response_model=List[CardRechargeRecordResponse], summary="查询充值记录")
async def get_recharge_records(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询会员卡的充值记录
    - 普通用户只能查询自己的记录
    - 管理员可以查询所有记录
    """
    # 查询会员卡
    card = db.query(MemberCard).filter(MemberCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="会员卡不存在")
    
    # 权限检查
    if current_user.role != "admin" and card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此记录")
    
    # 查询充值记录
    records = db.query(CardRechargeRecord).filter(
        CardRechargeRecord.member_card_id == card_id
    ).order_by(CardRechargeRecord.created_at.desc()).all()
    
    return records
