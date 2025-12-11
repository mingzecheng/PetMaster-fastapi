import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import payment as crud_payment
from app.database import get_db
from app.models.payment import PaymentStatus, PaymentMethod, Payment
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentRequestResponse
from app.services.payment_service import PaymentService
from app.utils.dependencies import get_current_active_user
from app.utils.exceptions import NotFoundError, ForbiddenError, AppException
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/payments", tags=["支付管理"])


@router.post("/alipay/create", response_model=PaymentRequestResponse, status_code=status.HTTP_201_CREATED,
             summary="创建支付宝支付请求")
async def create_alipay_payment(
        payment_in: PaymentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    创建支付宝支付请求

    - **amount**: 支付金额（单位：元）
    - **subject**: 商品标题
    - **description**: 商品描述（可选）
    - **related_id**: 关联ID（预约ID、商品ID等）
    - **related_type**: 关联类型（appointment、product等）
    """
    logger.info(f"创建支付请求: user_id={current_user.id}, amount={payment_in.amount}")

    # 使用统一支付服务创建支付
    result = PaymentService.create_alipay_payment(
        db=db,
        user_id=current_user.id,
        amount=payment_in.amount,
        subject=payment_in.subject,
        description=payment_in.description,
        related_id=payment_in.related_id,
        related_type=payment_in.related_type
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
        message=result.message or "支付请求已生成"
    )


@router.get("/{out_trade_no}/status", summary="查询支付状态")
async def query_payment_status(
        out_trade_no: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """查询支付状态"""
    logger.info(f"查询支付状态: out_trade_no={out_trade_no}, user_id={current_user.id}")

    # 使用服务层查询（自动同步支付宝状态）
    payment = PaymentService.query_payment_status(db, out_trade_no, sync_from_alipay=True)

    if not payment:
        raise NotFoundError("支付记录不存在")

    # 权限检查：普通会员只能查看自己的支付
    if current_user.role == "member" and payment.user_id != current_user.id:
        raise ForbiddenError("无权查看此支付记录")

    return {
        "out_trade_no": payment.out_trade_no,
        "status": payment.status,
        "amount": str(payment.amount),
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
    payment = PaymentService.query_payment_status(db, out_trade_no, sync_from_alipay=True)

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


@router.post("/alipay/notify", summary="支付宝异步通知")
async def alipay_notify(
        data: dict,
        db: Session = Depends(get_db)
):
    """处理支付宝异步通知"""
    logger.info(f"收到支付宝异步通知")

    # 使用服务层处理回调
    result = PaymentService.handle_alipay_callback(db, data)

    return result
