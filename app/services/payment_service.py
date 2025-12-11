"""
统一支付服务模块

封装支付创建、状态查询、回调处理等逻辑，
支持支付宝支付，预留微信支付扩展接口。
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.member import MemberCard, CardRechargeRecord
from app.utils.alipay import get_alipay_client
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


class PaymentResult:
    """支付创建结果"""

    def __init__(
        self,
        success: bool,
        payment_id: int = None,
        out_trade_no: str = None,
        pay_url: str = None,
        qr_code: str = None,
        message: str = None,
        error: str = None
    ):
        self.success = success
        self.payment_id = payment_id
        self.out_trade_no = out_trade_no
        self.pay_url = pay_url
        self.qr_code = qr_code
        self.message = message
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "payment_id": self.payment_id,
            "out_trade_no": self.out_trade_no,
            "pay_url": self.pay_url,
            "qr_code": self.qr_code,
            "message": self.message,
            "error": self.error
        }


class PaymentService:
    """
    统一支付服务

    提供支付创建、状态查询、回调处理等功能。
    当前支持支付宝，预留微信支付扩展接口。
    """

    @staticmethod
    def generate_trade_no(prefix: str, user_id: int) -> str:
        """
        生成商户订单号

        Args:
            prefix: 订单号前缀（如 PET、CARD）
            user_id: 用户ID

        Returns:
            格式化的订单号
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = uuid.uuid4().hex[:8]
        return f"{prefix}_{user_id}_{timestamp}_{random_suffix}"

    @staticmethod
    def create_alipay_payment(
        db: Session,
        user_id: int,
        amount: Decimal,
        subject: str,
        description: str = None,
        related_id: int = None,
        related_type: str = None,
        return_url: str = None,
        notify_url: str = None
    ) -> PaymentResult:
        """
        创建支付宝支付

        Args:
            db: 数据库会话
            user_id: 用户ID
            amount: 支付金额
            subject: 商品标题
            description: 商品描述
            related_id: 关联ID（如会员卡ID、商品ID）
            related_type: 关联类型（如 member_card_recharge、product）
            return_url: 支付完成后跳转地址
            notify_url: 异步通知地址

        Returns:
            PaymentResult 支付创建结果
        """
        # 生成订单号
        out_trade_no = PaymentService.generate_trade_no("PAY", user_id)

        logger.info(f"创建支付宝支付: user_id={user_id}, amount={amount}, out_trade_no={out_trade_no}")

        try:
            # 创建支付记录
            payment = Payment(
                user_id=user_id,
                out_trade_no=out_trade_no,
                amount=amount,
                status=PaymentStatus.PENDING,
                method=PaymentMethod.ALIPAY,
                subject=subject,
                description=description,
                related_id=related_id,
                related_type=related_type
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)

            logger.info(f"支付记录创建成功: payment_id={payment.id}")

            # 获取支付宝客户端
            alipay_client = get_alipay_client()

            # 检查客户端是否初始化
            if not alipay_client.client_initialized:
                logger.error("支付宝客户端未初始化，请检查密钥配置")
                return PaymentResult(
                    success=False,
                    error="支付宝客户端未初始化，请检查密钥配置"
                )

            # 设置回调地址（优先使用传入的参数，否则使用配置中的默认值）
            if not return_url:
                return_url = settings.ALIPAY_RETURN_URL or ""
            if not notify_url:
                notify_url = settings.ALIPAY_NOTIFY_URL or ""
            
            logger.info(f"支付回调地址配置: return_url={return_url}, notify_url={notify_url}")

            # 创建支付请求
            result = alipay_client.create_payment(
                out_trade_no=out_trade_no,
                total_amount=str(amount),
                subject=subject,
                description=description or "",
                return_url=return_url,
                notify_url=notify_url
            )

            if result:
                payment.response_data = str(result)
                db.add(payment)
                db.commit()

                logger.info(f"支付请求创建成功: {out_trade_no}")

                return PaymentResult(
                    success=True,
                    payment_id=payment.id,
                    out_trade_no=out_trade_no,
                    pay_url=result.get("pay_url", ""),
                    message="支付请求已生成，请完成支付"
                )
            else:
                logger.error(f"支付创建失败: {out_trade_no}")
                return PaymentResult(
                    success=False,
                    error="创建支付请求失败，请稍后重试"
                )

        except Exception as e:
            logger.error(f"创建支付异常: {str(e)}")
            db.rollback()
            return PaymentResult(
                success=False,
                error=str(e)
            )

    @staticmethod
    def query_payment_status(
        db: Session,
        out_trade_no: str,
        sync_from_alipay: bool = True
    ) -> Optional[Payment]:
        """
        查询支付状态

        Args:
            db: 数据库会话
            out_trade_no: 商户订单号
            sync_from_alipay: 是否从支付宝同步最新状态

        Returns:
            支付记录，不存在返回 None
        """
        payment = db.query(Payment).filter(Payment.out_trade_no == out_trade_no).first()

        if not payment:
            return None

        # 如果是待支付状态且需要同步，从支付宝查询
        if payment.status == PaymentStatus.PENDING and sync_from_alipay:
            alipay_client = get_alipay_client()

            if alipay_client.client_initialized:
                result = alipay_client.query_payment(out_trade_no=out_trade_no)

                if result and result.get("trade_status") == "TRADE_SUCCESS":
                    payment.status = PaymentStatus.PAID
                    payment.trade_no = result.get("trade_no")
                    payment.response_data = str(result)
                    payment.paid_at = datetime.now()
                    db.add(payment)
                    db.commit()

                    logger.info(f"支付状态同步成功: {out_trade_no} -> PAID")

                    # 处理支付成功后的业务逻辑
                    PaymentService._process_payment_success(db, payment)

        return payment

    @staticmethod
    def handle_alipay_callback(
        db: Session,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        处理支付宝异步通知

        Args:
            db: 数据库会话
            data: 通知数据

        Returns:
            处理结果
        """
        try:
            logger.info(f"处理支付宝回调: {data}")

            # 验证通知签名
            alipay_client = get_alipay_client()
            if not alipay_client.verify_notify(data):
                logger.warning("支付宝通知验证失败")
                return {"code": "FAIL", "message": "验证失败"}

            # 获取订单号
            out_trade_no = data.get("out_trade_no")
            payment = db.query(Payment).filter(Payment.out_trade_no == out_trade_no).first()

            if not payment:
                logger.warning(f"支付记录不存在: {out_trade_no}")
                return {"code": "FAIL", "message": "支付记录不存在"}

            # 检查是否已处理
            if payment.status == PaymentStatus.PAID:
                logger.info(f"支付已处理: {out_trade_no}")
                return {"code": "SUCCESS", "message": "已处理"}

            # 更新支付状态
            trade_status = data.get("trade_status")
            if trade_status == "TRADE_SUCCESS":
                payment.status = PaymentStatus.PAID
                payment.trade_no = data.get("trade_no")
                payment.notify_data = str(data)
                payment.paid_at = datetime.now()

                db.add(payment)
                db.commit()

                logger.info(f"支付成功: {out_trade_no}")

                # 处理支付成功后的业务逻辑
                PaymentService._process_payment_success(db, payment)

            elif trade_status in ["TRADE_CLOSED", "TRADE_FINISHED"]:
                payment.status = PaymentStatus.CANCELLED
                payment.notify_data = str(data)
                db.add(payment)
                db.commit()

                logger.info(f"支付取消/完成: {out_trade_no}")

            return {"code": "SUCCESS", "message": "处理成功"}

        except Exception as e:
            logger.error(f"处理支付宝回调异常: {str(e)}")
            return {"code": "FAIL", "message": str(e)}

    @staticmethod
    def _process_payment_success(db: Session, payment: Payment) -> bool:
        """
        处理支付成功后的业务逻辑

        根据 related_type 执行不同的业务处理：
        - member_card_recharge: 更新会员卡余额
        - product: 创建订单记录等

        Args:
            db: 数据库会话
            payment: 支付记录

        Returns:
            处理是否成功
        """
        try:
            related_type = payment.related_type

            if related_type == "member_card_recharge":
                return PaymentService._process_member_card_recharge(db, payment)
            elif related_type == "product":
                # TODO: 商品购买处理
                logger.info(f"商品购买支付成功: payment_id={payment.id}")
                return True
            else:
                logger.warning(f"未知的关联类型: {related_type}")
                return True

        except Exception as e:
            logger.error(f"处理支付成功业务异常: {str(e)}")
            return False

    @staticmethod
    def _process_member_card_recharge(db: Session, payment: Payment) -> bool:
        """
        处理会员卡充值

        Args:
            db: 数据库会话
            payment: 支付记录

        Returns:
            处理是否成功
        """
        try:
            card_id = payment.related_id
            if not card_id:
                logger.error(f"会员卡充值缺少 card_id: payment_id={payment.id}")
                return False

            # 获取会员卡
            card = db.query(MemberCard).filter(MemberCard.id == card_id).first()
            if not card:
                logger.error(f"会员卡不存在: card_id={card_id}")
                return False

            # 记录充值前余额
            balance_before = card.balance
            balance_after = balance_before + payment.amount

            # 更新会员卡余额
            card.balance = balance_after
            card.total_recharge += payment.amount

            # 创建充值记录
            recharge_record = CardRechargeRecord(
                member_card_id=card_id,
                amount=payment.amount,
                balance_before=balance_before,
                balance_after=balance_after,
                payment_method="alipay",
                transaction_no=payment.trade_no,
                operator_id=None,  # 用户自助充值
                remark="支付宝在线充值"
            )

            db.add(card)
            db.add(recharge_record)
            db.commit()

            logger.info(
                f"会员卡充值成功: card_id={card_id}, "
                f"amount={payment.amount}, balance={balance_after}"
            )

            return True

        except Exception as e:
            logger.error(f"处理会员卡充值异常: {str(e)}")
            db.rollback()
            return False


# 创建全局服务实例
payment_service = PaymentService()
