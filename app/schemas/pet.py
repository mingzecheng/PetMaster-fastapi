from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from app.models.pet import PetGender


class PetBase(BaseModel):
    """宠物基础Schema"""
    name: str = Field(..., max_length=50, description="宠物名称")
    species: Optional[str] = Field(None, max_length=50, description="宠物种类")
    breed: Optional[str] = Field(None, max_length=50, description="品种")
    gender: Optional[PetGender] = Field(None, description="性别")
    birthday: Optional[date] = Field(None, description="生日")
    weight: Optional[float] = Field(None, ge=0, le=999.99, description="体重(kg)")
    health_status: Optional[str] = Field(None, max_length=255, description="健康状况")
    image_url: Optional[str] = Field(None, max_length=500, description="宠物图片URL")


class PetCreate(PetBase):
    """宠物创建Schema"""
    owner_id: int = Field(..., description="宠物主人ID")


class PetUpdate(BaseModel):
    """宠物更新Schema"""
    name: Optional[str] = Field(None, max_length=50, description="宠物名称")
    species: Optional[str] = Field(None, max_length=50, description="宠物种类")
    breed: Optional[str] = Field(None, max_length=50, description="品种")
    gender: Optional[PetGender] = Field(None, description="性别")
    birthday: Optional[date] = Field(None, description="生日")
    weight: Optional[float] = Field(None, ge=0, le=999.99, description="体重(kg)")
    health_status: Optional[str] = Field(None, max_length=255, description="健康状况")
    image_url: Optional[str] = Field(None, max_length=500, description="宠物图片URL")


class PetResponse(PetBase):
    """宠物响应Schema"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PetHealthRecordBase(BaseModel):
    """健康记录基础Schema"""
    record_date: date = Field(..., description="记录日期")
    description: Optional[str] = Field(None, description="健康描述")
    veterinarian: Optional[str] = Field(None, max_length=50, description="兽医姓名")


class PetHealthRecordCreate(PetHealthRecordBase):
    """健康记录创建Schema"""
    pet_id: int = Field(..., description="宠物ID")


class HealthRecordCreate(PetHealthRecordCreate):
    """健康记录创建Schema（兼容别名）"""
    pass


class HealthRecordUpdate(BaseModel):
    """健康记录更新Schema"""
    record_date: Optional[date] = Field(None, description="记录日期")
    description: Optional[str] = Field(None, description="健康描述")
    veterinarian: Optional[str] = Field(None, max_length=50, description="兽医姓名")


class PetHealthRecordResponse(PetHealthRecordBase):
    """健康记录响应Schema"""
    id: int
    pet_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthRecordResponse(PetHealthRecordResponse):
    """健康记录响应Schema（兼容别名）"""
    pass
