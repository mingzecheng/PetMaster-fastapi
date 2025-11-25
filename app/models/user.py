from sqlalchemy import Column, BigInteger, String, Enum, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    STAFF = "staff"
    MEMBER = "member"


class User(Base):
    """用户与会员表模型"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='用户ID')
    username = Column(String(50), unique=True, nullable=False, index=True, comment='用户名')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    mobile = Column(String(20), unique=True, index=True, comment='手机号')
    email = Column(String(100), unique=True, index=True, comment='邮箱')
    role = Column(Enum(UserRole, native_enum=False), default=UserRole.MEMBER, comment='角色：管理员/员工/会员')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系
    pets = relationship("Pet", back_populates="owner", cascade="all, delete-orphan")
    appointments_as_staff = relationship("Appointment", foreign_keys="Appointment.staff_id", back_populates="staff")
    boarding_as_staff = relationship("Boarding", foreign_keys="Boarding.staff_id", back_populates="staff")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
