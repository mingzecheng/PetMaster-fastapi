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
from app.utils.dependencies import get_current_user, require_admin, get_current_active_user
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
    - 用户注销会员卡后可重新办卡
    """
    # 检查用户是否存在
    user = db.query(User).filter(User.id == card_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查用户是否已有会员卡（只会查询到active或frozen状态的卡）
    existing_card = db.query(MemberCard).filter(MemberCard.user_id == card_in.user_id).first()
    if existing_card:
        status_text = {
            "active": "正常使用中",
            "frozen": "已冻结",
            "cancelled": "已注销"
        }.get(existing_card.status, existing_card.status)
        raise HTTPException(
            status_code=400, 
            detail=f"用户已有会员卡（卡号: {existing_card.card_number}，状态: {status_text}）"
        )
    
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
    current_user: User = Depends(get_current_active_user)
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
    current_user: User = Depends(get_current_active_user)
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


@router.post("/{card_id}/freeze", response_model=MemberCardResponse, summary="冻结会员卡")
async def freeze_member_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    冻结会员卡
    - 仅管理员可操作
    - 冻结后无法充值和消费
    """
    card = db.query(MemberCard).filter(MemberCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="会员卡不存在")
    
    if card.status == "frozen":
        raise HTTPException(status_code=400, detail="会员卡已处于冻结状态")
    
    if card.status == "cancelled":
        raise HTTPException(status_code=400, detail="会员卡已注销,无法冻结")
    
    card.status = "frozen"
    db.commit()
    db.refresh(card)
    
    return card


@router.post("/{card_id}/unfreeze", response_model=MemberCardResponse, summary="解冻会员卡")
async def unfreeze_member_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    解冻会员卡
    - 仅管理员可操作
    - 解冻后恢复正常使用
    """
    card = db.query(MemberCard).filter(MemberCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="会员卡不存在")
    
    if card.status != "frozen":
        raise HTTPException(status_code=400, detail="会员卡未冻结,无需解冻")
    
    card.status = "active"
    db.commit()
    db.refresh(card)
    
    return card


@router.post("/{card_id}/cancel", summary="注销会员卡")
async def cancel_member_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    注销会员卡
    - 仅管理员可操作
    - 注销前需要清空余额
    - 注销后会删除会员卡记录，用户可重新办卡
    - 历史充值记录会一并删除（级联删除）
    """
    card = db.query(MemberCard).filter(MemberCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="会员卡不存在")
    
    
    if card.balance > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"会员卡余额为 ¥{card.balance},请先完成退款"
        )
    
    # 保存卡号用于响应
    card_number = card.card_number
    user_id = card.user_id
    
    # 删除会员卡记录（级联删除充值记录）
    db.delete(card)
    
    # 重置用户会员信息（等级和积分）
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        # 如果用户有积分，添加一条清零记录
        if user.points > 0:
            from app.models.member import PointRecord, PointRecordType
            
            point_record = PointRecord(
                user_id=user_id,
                points=-user.points,  # 扣除所有积分
                balance=0,
                type=PointRecordType.ADJUST,
                reason="会员卡注销，积分清零",
                operator_id=current_user.id
            )
            db.add(point_record)
        
        user.member_level_id = None
        user.points = 0
        user.total_points = 0
        db.add(user)
        
    db.commit()
    
    return {
        "message": f"会员卡 {card_number} 已注销并删除，会员等级和积分已重置，用户可重新办卡", 
        "card_id": card_id
    }


from pydantic import BaseModel


class CardRechargePaymentRequest(BaseModel):
    """会员卡充值支付请求"""
    amount: Decimal


@router.post("/{card_id}/payment/create", summary="创建会员卡充值支付(小程序)")
async def create_card_recharge_payment(
    card_id: int,
    request: CardRechargePaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建会员卡充值支付请求（供小程序用户自助充值）

    - 用户只能为自己的会员卡充值
    - 创建支付宝支付请求
    - 返回支付URL供用户扫码或跳转支付
    - 支付成功后通过统一回调自动更新余额
    """
    from app.services.payment_service import PaymentService

    amount = request.amount

    # 查询会员卡
    card = db.query(MemberCard).filter(MemberCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="会员卡不存在")

    # 权限检查：用户只能为自己的卡充值
    if current_user.role == "member" and card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权为此会员卡充值")

    if card.status != "active":
        raise HTTPException(status_code=400, detail="会员卡状态异常，无法充值")

    # 使用统一支付服务创建支付
    result = PaymentService.create_alipay_payment(
        db=db,
        user_id=current_user.id,
        amount=amount,
        subject=f"会员卡充值 - {card.card_number}",
        description=f"为会员卡{card.card_number}充值{amount}元",
        related_id=card_id,
        related_type="member_card_recharge"
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "创建支付请求失败")

    return {
        "payment_id": result.payment_id,
        "out_trade_no": result.out_trade_no,
        "pay_url": result.pay_url or "",
        "qr_code": result.qr_code or "",  # 添加二维码字段
        "amount": str(amount),
        "message": result.message or "支付请求已创建"
    }


@router.get("/{card_id}/payment/{out_trade_no}/status", summary="查询充值支付状态")
async def query_card_recharge_payment_status(
    card_id: int,
    out_trade_no: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询会员卡充值支付状态

    - 用户只能查询自己的支付
    - 自动同步支付宝最新状态
    - 支付成功后自动更新会员卡余额
    """
    from app.services.payment_service import PaymentService

    # 查询会员卡
    card = db.query(MemberCard).filter(MemberCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="会员卡不存在")

    # 权限检查
    if current_user.role == "member" and card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此支付记录")

    # 使用服务层查询（自动同步状态和处理充值）
    payment = PaymentService.query_payment_status(db, out_trade_no, sync_from_alipay=True)

    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")

    return {
        "out_trade_no": payment.out_trade_no,
        "status": payment.status.value if hasattr(payment.status, 'value') else payment.status,
        "amount": str(payment.amount),
        "created_at": payment.created_at,
        "paid_at": payment.paid_at
    }

