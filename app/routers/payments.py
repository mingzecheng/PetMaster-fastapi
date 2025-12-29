import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import payment as crud_payment
from app.database import get_db
from app.models.payment import PaymentStatus, PaymentMethod, Payment
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentRequestResponse, CombinedPaymentCreate
from app.services.payment_service import PaymentService
from app.utils.dependencies import get_current_active_user
from app.utils.exceptions import NotFoundError, ForbiddenError, AppException
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/payments", tags=["支付管理"])


@router.post("/create", response_model=PaymentRequestResponse, status_code=status.HTTP_201_CREATED,
             summary="创建支付请求")
async def create_payment(
        payment_in: PaymentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    创建支付请求（Mock模式）

    - **amount**: 支付金额（单位：元）
    - **subject**: 商品标题
    - **description**: 商品描述（可选）
    - **related_id**: 关联ID（预约ID、商品ID等）
    - **related_type**: 关联类型（appointment、product等）
    """
    logger.info(f"创建支付请求: user_id={current_user.id}, amount={payment_in.amount}")

    # 使用统一支付服务创建支付（Mock模式）
    result = PaymentService.create_alipay_payment(
        db=db,
        user_id=current_user.id,
        amount=payment_in.amount,
        subject=payment_in.subject,
        description=payment_in.description,
        related_id=payment_in.related_id,
        related_type=payment_in.related_type,
        notify_url=""  # Mock模式不需要notify_url
    )

    if not result.success:
        raise AppException(result.error or "创建支付请求失败", 500)

    return PaymentRequestResponse(
        payment_id=result.payment_id,
        out_trade_no=result.out_trade_no,
        amount=str(payment_in.amount),
        subject=payment_in.subject,
        qr_code=result.qr_code or "",
        pay_url=result.pay_url or "",
        status="pending",
        message=result.message or "支付请求已生成（Mock模式）"
    )


@router.get("/{out_trade_no}/status", summary="查询支付状态")
async def query_payment_status(
        out_trade_no: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """查询支付状态"""
    logger.info(f"查询支付状态: out_trade_no={out_trade_no}, user_id={current_user.id}")

    # 使用服务层查询
    payment = PaymentService.query_payment_status(db, out_trade_no, sync_from_alipay=False)

    if not payment:
        raise NotFoundError("支付记录不存在")

    # 权限检查：普通会员只能查看自己的支付
    if current_user.role == "member" and payment.user_id != current_user.id:
        raise ForbiddenError("无权查看此支付记录")

    return {
        "out_trade_no": payment.out_trade_no,
        "status": payment.status,
        "amount": str(payment.amount),
        "subject": payment.subject,
        "description": payment.description,
        "created_at": payment.created_at,
        "paid_at": payment.paid_at
    }


@router.get("/{out_trade_no}/poll", summary="轮询支付状态")
async def poll_payment_status(
        out_trade_no: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    轮询支付状态（前端定时调用）

    与 /status 接口类似，但更轻量：
    - 仅返回状态和是否完成
    - 建议每 3 秒轮询一次
    """
    payment = PaymentService.query_payment_status(db, out_trade_no, sync_from_alipay=False)

    if not payment:
        raise NotFoundError("支付记录不存在")

    # 权限检查
    if current_user.role == "member" and payment.user_id != current_user.id:
        raise ForbiddenError("无权查看此支付记录")

    return {
        "out_trade_no": payment.out_trade_no,
        "status": payment.status.value,
        "is_paid": payment.status == PaymentStatus.PAID,
        "amount": str(payment.amount)
    }


@router.get("/", response_model=List[PaymentResponse], summary="获取支付列表")
async def read_payments(
        skip: int = 0,
        limit: int = 100,
        pay_status: PaymentStatus = None,
        user_id: int = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取支付列表"""
    logger.info(f"获取支付列表: user_id={current_user.id}, status={pay_status}")

    if current_user.role == "member":
        # 普通会员只能查看自己的支付
        if pay_status:
            payments = db.query(Payment).filter(
                Payment.user_id == current_user.id,
                Payment.status == pay_status
            ).offset(skip).limit(limit).all()
        else:
            payments = crud_payment.get_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    else:
        # 员工和管理员可以查看所有支付
        if pay_status:
            payments = crud_payment.get_by_status(db, status=pay_status, skip=skip, limit=limit)
        elif user_id:
            payments = crud_payment.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
        else:
            payments = crud_payment.get_multi(db, skip=skip, limit=limit)

    logger.info(f"获取支付列表成功: count={len(payments)}")
    return payments




@router.post("/combined", summary="创建组合支付（积分+会员卡+支付宝）")
async def create_combined_payment(
        payment_in: CombinedPaymentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    创建组合支付（积分+会员卡余额+支付宝）
    
    支付优先级：积分 → 会员卡余额 → 支付宝
    
    - **amount**: 支付金额（单位：元）
    - **subject**: 商品标题
    - **related_id**: 关联ID（预约ID、寄养ID等）
    - **related_type**: 关联类型（appointment、boarding等）
    - **use_card_balance**: 是否使用会员卡余额（默认true）
    - **use_points**: 使用积分数量（默认0，100积分=1元）
    
    返回：
    - **points_used**: 使用的积分数量
    - **points_deduction**: 积分抵扣金额
    - **card_used**: 使用的会员卡余额
    - **alipay_amount**: 需要支付宝支付的金额
    - **fully_paid**: 是否已全额支付（true表示无需跳转支付宝）
    - **pay_url**: 支付URL（如需支付宝）
    - **out_trade_no**: 支付订单号（如需支付宝）
    """
    from decimal import Decimal
    
    logger.info(f"创建组合支付: user_id={current_user.id}, amount={payment_in.amount}, use_points={payment_in.use_points}, use_card={payment_in.use_card_balance}")
    
    try:
        result = PaymentService.create_combined_payment(
            db=db,
            user_id=current_user.id,
            amount=Decimal(str(payment_in.amount)),
            subject=payment_in.subject,
            related_id=payment_in.related_id,
            related_type=payment_in.related_type,
            use_card_balance=payment_in.use_card_balance,
            use_points=payment_in.use_points
        )
        
        logger.info(f"组合支付创建成功: user_id={current_user.id}, points={result['points_used']}, card={result['card_used']}, alipay={result['alipay_amount']}")
        return result
        
    except Exception as e:
        logger.error(f"创建组合支付失败: {str(e)}")
        raise AppException(message=f"创建组合支付失败: {str(e)}")

