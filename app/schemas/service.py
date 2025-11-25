from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ServiceBase(BaseModel):
    """服务基础Schema"""
    name: str = Field(..., max_length=100, description="服务名称")
    description: Optional[str] = Field(None, description="服务描述")
    price: Decimal = Field(..., ge=0, description="服务价格")
    duration_minutes: Optional[int] = Field(None, ge=0, description="服务时閤（分钟）")


class ServiceCreate(ServiceBase):
    """服务创建Schema"""
    pass


class ServiceUpdate(BaseModel):
    """服务更新Schema"""
    name: Optional[str] = Field(None, max_length=100, description="服务名称")
    description: Optional[str] = Field(None, description="服务描述")
    price: Optional[Decimal] = Field(None, ge=0, description="服务价格")
    duration_minutes: Optional[int] = Field(None, ge=0, description="服务时閤（分钟）")


class ServiceResponse(ServiceBase):
    """服务响应Schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
