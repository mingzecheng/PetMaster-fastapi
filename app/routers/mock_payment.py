"""
Mock支付路由
用于开发测试时模拟支付流程
"""
from fastapi import APIRouter,Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.utils.dependencies import get_current_active_user
from app.utils.logger import get_logger
from app.services.payment_service import PaymentService

logger = get_logger(__name__)

router = APIRouter(prefix="/mock-payment", tags=["Mock支付"])


class MockPaymentConfirm(BaseModel):
    """Mock支付确认请求"""
    out_trade_no: str


@router.post("/confirm", summary="确认Mock支付")
async def confirm_mock_payment(
    request: MockPaymentConfirm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    确认Mock支付（仅在PAYMENT_MODE=mock时可用）
    
    模拟支付宝支付成功的回调流程
    """
    from app.config import settings
    
    if settings.PAYMENT_MODE != "mock":
        raise HTTPException(status_code=403, detail="Mock支付功能未启用")
    
    logger.info(f"[Mock支付] 确认支付: {request.out_trade_no}")
    
    # 查询支付记录
    payment = db.query(Payment).filter(
        Payment.out_trade_no == request.out_trade_no
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="支付记录不存在")
    
    # 权限检查
    if current_user.role == "member" and payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此支付")
    
    # 检查支付状态
    if payment.status != PaymentStatus.PENDING:
        return {
            "success": False,
            "message": f"支付状态异常: {payment.status}",
            "status": payment.status
        }
    
    # 模拟支付宝回调数据
    mock_notify_data = {
        "trade_no": f"MOCK_{request.out_trade_no}",
        "out_trade_no": request.out_trade_no,
        "trade_status": "TRADE_SUCCESS",
        "total_amount": str(payment.amount),
        "gmt_payment": "2025-12-15 17:55:00"
    }
    
    # 更新支付状态为已支付
    from datetime import datetime
    payment.status = PaymentStatus.PAID
    payment.trade_no = mock_notify_data["trade_no"]
    payment.notify_data = str(mock_notify_data)
    payment.paid_at = datetime.now()  # 设置支付完成时间
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    logger.info(f"[Mock支付] 支付状态已更新为PAID: {request.out_trade_no}")
    
    # 处理支付成功后的业务逻辑
    PaymentService._process_payment_success(db, payment)
    
    logger.info(f"[Mock支付] 业务处理完成: {request.out_trade_no}")
    
    return {
        "success": True,
        "message": "Mock支付确认成功",
        "out_trade_no": request.out_trade_no,
        "status": payment.status
    }
