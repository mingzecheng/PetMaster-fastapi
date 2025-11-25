from sqlalchemy import Column, BigInteger, String, Integer, DECIMAL, Boolean, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PointRecordType(str, enum.Enum):
    """积分记录类型枚举"""
    EARN = "earn"  # 获得积分
    USE = "use"    # 使用积分
    ADJUST = "adjust"  # 手动调整


class MemberLevel(Base):
    """会员等级表模型"""
    __tablename__ = "member_levels"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='等级ID')
    name = Column(String(50), nullable=False, unique=True, comment='等级名称')
    level = Column(Integer, nullable=False, unique=True, comment='等级序号(数字越大等级越高)')
    min_points = Column(Integer, default=0, comment='升级所需最低累计积分')
    discount_rate = Column(DECIMAL(3, 2), default=1.00, comment='折扣率(0.90表示9折)')
    icon = Column(String(100), comment='等级图标')
    color = Column(String(20), comment='等级颜色')
    description = Column(String(255), comment='等级描述')
    benefits = Column(Text, comment='等级权益(JSON格式)')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系
    users = relationship("User", back_populates="member_level")

    def __repr__(self):
        return f"<MemberLevel(id={self.id}, name={self.name}, level={self.level})>"


class PointRecord(Base):
    """积分记录表模型"""
    __tablename__ = "point_records"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='记录ID')
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, comment='用户ID')
    points = Column(Integer, nullable=False, comment='积分变动(正数为增加，负数为减少)')
    balance = Column(Integer, default=0, comment='变动后积分余额')
    type = Column(String(50), nullable=False, comment='类型: earn/use/adjust')
    reason = Column(String(255), comment='原因描述')
    transaction_id = Column(BigInteger, ForeignKey('transactions.id', ondelete='SET NULL'), comment='关联交易ID')
    operator_id = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), comment='操作员ID(手动调整时)')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')

    # 关系
    user = relationship("User", foreign_keys=[user_id], back_populates="point_records")
    transaction = relationship("Transaction", back_populates="point_records")
    operator = relationship("User", foreign_keys=[operator_id])

    def __repr__(self):
        return f"<PointRecord(id={self.id}, user_id={self.user_id}, points={self.points})>"


class MemberCard(Base):
    """会员卡表模型"""
    __tablename__ = "member_cards"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='会员卡ID')
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True, comment='用户ID')
    card_number = Column(String(20), unique=True, nullable=False, index=True, comment='会员卡号')
    balance = Column(DECIMAL(10, 2), default=0.00, comment='当前余额')
    total_recharge = Column(DECIMAL(10, 2), default=0.00, comment='累计充值金额')
    total_consumption = Column(DECIMAL(10, 2), default=0.00, comment='累计消费金额')
    status = Column(String(20), default='active', comment='状态: active/frozen/cancelled')
    activated_at = Column(TIMESTAMP, server_default=func.now(), comment='激活时间')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系
    user = relationship("User", back_populates="member_card")
    recharge_records = relationship("CardRechargeRecord", back_populates="member_card", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MemberCard(id={self.id}, card_number={self.card_number}, balance={self.balance})>"


class CardRechargeRecord(Base):
    """会员卡充值记录表模型"""
    __tablename__ = "card_recharge_records"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='充值记录ID')
    member_card_id = Column(BigInteger, ForeignKey('member_cards.id', ondelete='CASCADE'), nullable=False, index=True, comment='会员卡ID')
    amount = Column(DECIMAL(10, 2), nullable=False, comment='充值金额')
    balance_before = Column(DECIMAL(10, 2), comment='充值前余额')
    balance_after = Column(DECIMAL(10, 2), comment='充值后余额')
    payment_method = Column(String(50), comment='支付方式')
    transaction_no = Column(String(100), comment='交易流水号')
    operator_id = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), comment='操作员ID')
    remark = Column(String(255), comment='备注')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')

    # 关系
    member_card = relationship("MemberCard", back_populates="recharge_records")
    operator = relationship("User")

    def __repr__(self):
        return f"<CardRechargeRecord(id={self.id}, amount={self.amount})>"
