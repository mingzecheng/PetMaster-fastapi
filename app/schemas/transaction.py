from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    """交易基础Schema"""
    user_id: int = Field(..., description="会员ID")
    type: TransactionType = Field(..., description="交易类型")
    related_id: Optional[int] = Field(None, description="关联ID")
    amount: Optional[Decimal] = Field(None, ge=0, description="交易金镡")
    points_change: int = Field(default=0, description="积分变化")


class TransactionCreate(TransactionBase):
    """交易创建Schema"""
    pass


class TransactionResponse(TransactionBase):
    """交易响应Schema"""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
