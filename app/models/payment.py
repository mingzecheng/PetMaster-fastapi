from sqlalchemy import Column, BigInteger, String, Enum, DECIMAL, Integer, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PaymentStatus(str, enum.Enum):
    """支付状态枚举"""
    PENDING = "pending"  # 待支付
    PAID = "paid"  # 已支付
    FAILED = "failed"  # 支付失败
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"  # 已退款


class PaymentMethod(str, enum.Enum):
    """支付方式枚举"""
    ALIPAY = "alipay"  # 支付宝
    WECHAT = "wechat"  # 微信
    CARD = "card"  # 银行卡
    CASH = "cash"  # 现金


class Payment(Base):
    """支付记录表模型"""
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='支付ID')
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
                     comment='用户ID')
    out_trade_no = Column(String(64), unique=True, nullable=False, index=True, comment='商户订单号')
    trade_no = Column(String(64), nullable=True, index=True, comment='第三方交易号（支付宝等）')
    amount = Column(DECIMAL(10, 2), nullable=False, comment='支付金额')
    status = Column(Enum(PaymentStatus, native_enum=False), default=PaymentStatus.PENDING, index=True,
                    comment='支付状态')
    method = Column(Enum(PaymentMethod, native_enum=False), nullable=False, comment='支付方式')
    subject = Column(String(255), nullable=False, comment='商品标题')
    description = Column(Text, nullable=True, comment='商品描述')
    related_id = Column(BigInteger, nullable=True, comment='关联ID（订单、预约等）')
    related_type = Column(String(32), nullable=True, comment='关联类型（order、appointment等）')
    response_data = Column(Text, nullable=True, comment='支付宝返回数据')
    notify_data = Column(Text, nullable=True, comment='异步通知数据')
    error_message = Column(Text, nullable=True, comment='错误信息')
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True, comment='创建时间')
    paid_at = Column(TIMESTAMP, nullable=True, comment='支付完成时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系
    user = relationship("User", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"
