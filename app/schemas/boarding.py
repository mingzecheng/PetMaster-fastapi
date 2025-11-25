from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from app.models.boarding import BoardingStatus


class BoardingBase(BaseModel):
    """寄养基础Schema"""
    pet_id: int = Field(..., description="宠物ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    daily_rate: Optional[Decimal] = Field(None, ge=0, description="每日费用")
    staff_id: Optional[int] = Field(None, description="负责员工ID")
    notes: Optional[str] = Field(None, max_length=500, description="备注")


class BoardingCreate(BoardingBase):
    """寄养创建Schema"""
    pass


class BoardingUpdate(BaseModel):
    """寄养更新Schema"""
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    daily_rate: Optional[Decimal] = Field(None, ge=0, description="每日费用")
    staff_id: Optional[int] = Field(None, description="负责员工ID")
    status: Optional[BoardingStatus] = Field(None, description="寄养状态")
    notes: Optional[str] = Field(None, max_length=500, description="备注")


class BoardingResponse(BoardingBase):
    """寄养响应Schema"""
    id: int
    status: BoardingStatus
    total_cost: Optional[Decimal] = Field(None, description="总费用")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
