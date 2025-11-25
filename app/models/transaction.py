from sqlalchemy import Column, BigInteger, Enum, DECIMAL, Integer, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TransactionType(str, enum.Enum):
    """交易类型枚举"""
    PURCHASE = "purchase"  # 购买商品
    SERVICE = "service"  # 服务消费
    POINTS_ADD = "points_add"  # 积分增加
    POINTS_DEDUCT = "points_deduct"  # 积分扣除


class Transaction(Base):
    """会员积分及消费记录表模型"""
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='交易ID')
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
                     comment='会员ID')
    type = Column(Enum(TransactionType, native_enum=False), nullable=False, index=True, comment='交易类型')
    related_id = Column(BigInteger, comment='关联ID：商品ID或服务ID')
    amount = Column(DECIMAL(10, 2), comment='交易金额')
    points_change = Column(Integer, default=0, comment='积分变化')
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True, comment='交易时间')

    # 关系
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, type={self.type}, amount={self.amount})>"
