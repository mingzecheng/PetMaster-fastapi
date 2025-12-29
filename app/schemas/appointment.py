from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    """预约基础Schema"""
    pet_id: int = Field(..., description="宠物ID")
    service_id: int = Field(..., description="服务ID")
    appointment_time: datetime = Field(..., description="预约时间")
    staff_id: Optional[int] = Field(None, description="员工ID")


class AppointmentCreate(AppointmentBase):
    """预约创建Schema"""
    pass


class AppointmentUpdate(BaseModel):
    """预约更新Schema"""
    appointment_time: Optional[datetime] = Field(None, description="预约时间")
    staff_id: Optional[int] = Field(None, description="员工ID")
    status: Optional[AppointmentStatus] = Field(None, description="预约状态")


class AppointmentCancelRequest(BaseModel):
    """预约取消请求Schema"""
    reason: Optional[str] = Field(None, max_length=200, description="取消原因")


class AppointmentResponse(AppointmentBase):
    """预约响应Schema"""
    id: int
    payment_id: Optional[int] = Field(None, description="支付记录ID")
    price: Optional[Decimal] = Field(None, description="服务价格快照")
    status: AppointmentStatus
    cancel_reason: Optional[str] = Field(None, description="取消原因")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

