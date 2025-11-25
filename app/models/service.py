from sqlalchemy import Column, BigInteger, String, Text, DECIMAL, Integer, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.database import Base


class Service(Base):
    """服务项目表模型"""
    __tablename__ = "services"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='服务ID')
    name = Column(String(100), nullable=False, index=True, comment='服务名称')
    description = Column(Text, comment='服务描述')
    price = Column(DECIMAL(10, 2), nullable=False, comment='服务价格')
    duration_minutes = Column(Integer, comment='服务时长（分钟）')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系
    appointments = relationship("Appointment", back_populates="service", cascade="all, delete-orphan",
                                passive_deletes=True)

    def __repr__(self):
        return f"<Service(id={self.id}, name={self.name}, price={self.price})>"
