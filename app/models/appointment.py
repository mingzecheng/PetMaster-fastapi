from sqlalchemy import Column, BigInteger, DateTime, Enum, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class AppointmentStatus(str, enum.Enum):
    """预约状态枚举"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Appointment(Base):
    """预约服务表模型"""
    __tablename__ = "appointments"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='预约ID')
    pet_id = Column(BigInteger, ForeignKey('pets.id', ondelete='CASCADE'), nullable=False, index=True, comment='宠物ID')
    service_id = Column(BigInteger, ForeignKey('services.id', ondelete='CASCADE'), nullable=False, index=True,
                        comment='服务ID')
    appointment_time = Column(DateTime, nullable=False, index=True, comment='预约时间')
    staff_id = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), index=True, comment='员工ID')
    status = Column(Enum(AppointmentStatus, native_enum=False), default=AppointmentStatus.PENDING, index=True,
                    comment='预约状态')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系
    pet = relationship("Pet", back_populates="appointments")
    service = relationship("Service", back_populates="appointments", passive_deletes=True)
    staff = relationship("User", foreign_keys=[staff_id], back_populates="appointments_as_staff")

    def __repr__(self):
        return f"<Appointment(id={self.id}, pet_id={self.pet_id}, status={self.status})>"
