from sqlalchemy import Column, BigInteger, Date, DECIMAL, Enum, TIMESTAMP, ForeignKey, String, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class BoardingStatus(str, enum.Enum):
    """寄养状态枚举"""
    PENDING = "pending"  # 待确认
    ACTIVE = "active"    # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class Boarding(Base):
    """寄养管理表模型"""
    __tablename__ = "boarding"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='寄养ID')
    pet_id = Column(BigInteger, ForeignKey('pets.id', ondelete='CASCADE'), nullable=False, index=True, comment='宠物ID')
    start_date = Column(Date, nullable=False, index=True, comment='寄养开始日期')
    end_date = Column(Date, nullable=False, index=True, comment='寄养结束日期')
    daily_rate = Column(DECIMAL(10, 2), comment='每日费用')
    total_cost = Column(DECIMAL(10, 2), comment='总费用')
    staff_id = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), index=True, comment='负责员工ID')
    status = Column(Enum(BoardingStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]), 
                    default=BoardingStatus.PENDING, index=True, comment='寄养状态')
    notes = Column(String(500), comment='备注')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系
    pet = relationship("Pet", back_populates="boarding")
    staff = relationship("User", foreign_keys=[staff_id], back_populates="boarding_as_staff")

    def __repr__(self):
        return f"<Boarding(id={self.id}, pet_id={self.pet_id}, status={self.status})>"
