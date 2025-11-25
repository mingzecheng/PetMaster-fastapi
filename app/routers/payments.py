from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse, PaymentRequestResponse
from app.models.user import User
from app.models.payment import PaymentStatus, PaymentMethod, Payment
from app.crud import payment as crud_payment
from app.utils.dependencies import get_current_active_user, require_staff
from app.utils.alipay import get_alipay_client
from app.utils.logger import get_logger
from app.utils.exceptions import NotFoundError, ForbiddenError, AppException
import uuid

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
    # 生成商户订单号
    out_trade_no = f"PET_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

    logger.info(f"开始创建支付宝支付请求: 用户ID={current_user.id}, 订单号={out_trade_no}")

    # 创建支付记录
    db_payment = Payment(
        user_id=current_user.id,
        out_trade_no=out_trade_no,
        amount=payment_in.amount,
        status=PaymentStatus.PENDING,
        method=PaymentMethod.ALIPAY,
        subject=payment_in.subject,
        description=payment_in.description,
        related_id=payment_in.related_id,
        related_type=payment_in.related_type
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    logger.info(f"支付记录创建成功: ID={db_payment.id}")

    # 调用支付宝API创建支付
    alipay_client = get_alipay_client()

    # 检查支付宝客户端是否初始化成功
    if not alipay_client.client_initialized:
        logger.warning(f"支付宝客户端未正常初始化，使用模拟支付模式")
        # 测试环境下，使用模拟支付信息返回
        return PaymentRequestResponse(
            payment_id=db_payment.id,
            out_trade_no=out_trade_no,
            amount=payment_in.amount,
            subject=payment_in.subject,
            qr_code="",
            pay_url=f"https://openapi.alipay.com/gateway.do?test_request={out_trade_no}",
            status="pending",
            message="支付请求已生成（模拟模式）"
        )

    # 构建支付宝支付请求
    result = alipay_client.create_payment(
        out_trade_no=out_trade_no,
        total_amount=str(payment_in.amount),
        subject=payment_in.subject,
        description=payment_in.description or "",
        return_url=f"http://localhost:3000/payment/return/{out_trade_no}",
        notify_url=f"http://localhost:8001/api/v1/payments/alipay/notify"
    )

    if result:
        # 保存支付宝返回数据
        db_payment.response_data = str(result)
        db.add(db_payment)
        db.commit()

        logger.info(f"支付宝支付请求创建成功: {out_trade_no}")

        return PaymentRequestResponse(
            payment_id=db_payment.id,
            out_trade_no=out_trade_no,
            amount=payment_in.amount,
            subject=payment_in.subject,
            qr_code=result.get("qr_code", ""),
            pay_url=result.get("pay_url", ""),
            status="pending",
            message="支付请求已生成，请使用支付宝扫码支付"
        )
    else:
        logger.error(f"支付宝支付请求创建失败: {out_trade_no}")
        raise AppException("创建支付请求失败，请稍后重试", 500)


@router.get("/{out_trade_no}/status", summary="查询支付状态")
async def query_payment_status(
        out_trade_no: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """查询支付状态"""
    logger.info(f"查询支付状态: 订单号={out_trade_no}, 用户ID={current_user.id}")

    payment = crud_payment.get_by_out_trade_no(db, out_trade_no=out_trade_no)

    if not payment:
        logger.warning(f"支付记录不存在: {out_trade_no}")
        raise NotFoundError("支付记录不存在")

    # 普通会员只能查看自己的支付
    if current_user.role == "member" and payment.user_id != current_user.id:
        logger.warning(f"无权查看支付记录: 用户ID={current_user.id}, 支付ID={payment.id}")
        raise ForbiddenError("无权查看此支付记录")

    # 如果是待支付状态，尝试从支付宝查询最新状态
    if payment.status == PaymentStatus.PENDING:
        logger.info(f"从支付宝查询支付状态: {out_trade_no}")
        alipay_client = get_alipay_client()

        # 检查支付宝客户端是否初始化成功
        if alipay_client.client_initialized:
            result = alipay_client.query_payment(out_trade_no=out_trade_no)

            if result and result.get("trade_status") == "TRADE_SUCCESS":
                # 更新支付状态
                payment.status = PaymentStatus.PAID
                payment.trade_no = result.get("trade_no")
                payment.response_data = str(result)
                payment.paid_at = datetime.now()
                db.add(payment)
                db.commit()
                logger.info(f"支付已完成: {out_trade_no}")
        else:
            logger.warning(f"支付宝客户端未初始化，无法查询支付状态")

    return {
        "out_trade_no": payment.out_trade_no,
        "status": payment.status,
        "amount": str(payment.amount),
        "created_at": payment.created_at,
        "paid_at": payment.paid_at
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
    logger.info(f"获取支付列表: 用户ID={current_user.id}, 状态={pay_status}, 用户={user_id}")

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

    logger.info(f"成功获取支付列表: 数量={len(payments)}")
    return payments


@router.post("/alipay/notify", summary="支付宝异步通知")
async def alipay_notify(
        data: dict,
        db: Session = Depends(get_db)
):
    """处理支付宝异步通知"""
    try:
        logger.info(f"收到支付宝异步通知: {data}")

        # 验证通知
        alipay_client = get_alipay_client()
        if not alipay_client.verify_notify(data):
            logger.warning(f"支付宝异步通知验证失败: {data}")
            return {"code": "FAIL", "message": "验证失败"}

        # 获取支付记录
        out_trade_no = data.get("out_trade_no")
        payment = crud_payment.get_by_out_trade_no(db, out_trade_no=out_trade_no)

        if not payment:
            logger.warning(f"支付记录不存在: {out_trade_no}")
            return {"code": "FAIL", "message": "支付记录不存在"}

        # 更新支付状态
        trade_status = data.get("trade_status")
        if trade_status == "TRADE_SUCCESS":
            payment.status = PaymentStatus.PAID
            payment.trade_no = data.get("trade_no")
            payment.notify_data = str(data)
            payment.paid_at = datetime.now()
            logger.info(f"支付成功: {out_trade_no}")
        elif trade_status in ["TRADE_CLOSED", "TRADE_FINISHED"]:
            payment.status = PaymentStatus.CANCELLED
            payment.notify_data = str(data)
            logger.info(f"支付取消或完成: {out_trade_no}")

        db.add(payment)
        db.commit()

        return {"code": "SUCCESS", "message": "处理成功"}
    except Exception as e:
        logger.error(f"处理支付宝异步通知异常: {str(e)}")
        return {"code": "FAIL", "message": str(e)}
