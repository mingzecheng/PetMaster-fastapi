from sqlalchemy import Column, BigInteger, String, Enum, Date, DECIMAL, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PetGender(str, enum.Enum):
    """宠物性别枚举"""
    MALE = "male"
    FEMALE = "female"


class Pet(Base):
    """宠物档案表模型"""
    __tablename__ = "pets"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='宠物ID')
    owner_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
                      comment='宠物主人ID')
    name = Column(String(50), nullable=False, comment='宠物名称')
    species = Column(String(50), comment='宠物种类（狗、猫等）')
    breed = Column(String(50), comment='品种')
    gender = Column(Enum(PetGender, native_enum=False), comment='性别')
    birthday = Column(Date, comment='生日')
    weight = Column(DECIMAL(5, 2), comment='体重(kg)')
    health_status = Column(String(255), comment='健康状况描述')
    image_url = Column(String(500), comment='宠物图片URL')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 关系
    owner = relationship("User", back_populates="pets")
    health_records = relationship("PetHealthRecord", back_populates="pet", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="pet", cascade="all, delete-orphan")
    boarding = relationship("Boarding", back_populates="pet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pet(id={self.id}, name={self.name}, species={self.species})>"


class PetHealthRecord(Base):
    """宠物健康记录表模型"""
    __tablename__ = "pet_health_records"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='健康记录ID')
    pet_id = Column(BigInteger, ForeignKey('pets.id', ondelete='CASCADE'), nullable=False, index=True, comment='宠物ID')
    record_date = Column(Date, nullable=False, comment='记录日期')
    description = Column(Text, comment='健康检查或治疗描述')
    veterinarian = Column(String(50), comment='兽医姓名')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')

    # 关系
    pet = relationship("Pet", back_populates="health_records")

    def __repr__(self):
        return f"<PetHealthRecord(id={self.id}, pet_id={self.pet_id}, date={self.record_date})>"
