from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ============ 会员等级 Schemas ============

class MemberLevelBase(BaseModel):
    """会员等级基础Schema"""
    name: str = Field(..., min_length=1, max_length=50, description="等级名称")
    level: int = Field(..., ge=0, description="等级序号")
    min_points: int = Field(default=0, ge=0, description="升级所需最低累计积分")
    discount_rate: Decimal = Field(default=Decimal("1.00"), ge=0, le=1, description="折扣率")
    icon: Optional[str] = Field(None, max_length=100, description="等级图标")
    color: Optional[str] = Field(None, max_length=20, description="等级颜色")
    description: Optional[str] = Field(None, max_length=255, description="等级描述")
    benefits: Optional[str] = Field(None, description="等级权益JSON")
    is_active: bool = Field(default=True, description="是否启用")


class MemberLevelCreate(MemberLevelBase):
    """创建会员等级Schema"""
    pass


class MemberLevelUpdate(BaseModel):
    """更新会员等级Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    level: Optional[int] = Field(None, ge=0)
    min_points: Optional[int] = Field(None, ge=0)
    discount_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    icon: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=255)
    benefits: Optional[str] = None
    is_active: Optional[bool] = None


class MemberLevelResponse(MemberLevelBase):
    """会员等级响应Schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ 积分记录 Schemas ============

class PointRecordBase(BaseModel):
    """积分记录基础Schema"""
    points: int = Field(..., description="积分变动")
    type: str = Field(..., description="类型: earn/use/adjust")
    reason: Optional[str] = Field(None, max_length=255, description="原因描述")


class PointRecordCreate(PointRecordBase):
    """创建积分记录Schema"""
    user_id: int = Field(..., description="用户ID")
    transaction_id: Optional[int] = Field(None, description="关联交易ID")


class PointRecordResponse(PointRecordBase):
    """积分记录响应Schema"""
    id: int
    user_id: int
    balance: int
    transaction_id: Optional[int]
    operator_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PointAdjust(BaseModel):
    """手动调整积分Schema"""
    points: int = Field(..., description="积分变动(正数增加,负数减少)")
    reason: str = Field(..., min_length=1, max_length=255, description="调整原因")


# ============ 会员卡 Schemas ============

class MemberCardBase(BaseModel):
    """会员卡基础Schema"""
    card_number: str = Field(..., min_length=1, max_length=20, description="会员卡号")


class MemberCardCreate(BaseModel):
    """创建会员卡Schema"""
    user_id: int = Field(..., description="用户ID")


class MemberCardResponse(MemberCardBase):
    """会员卡响应Schema"""
    id: int
    user_id: int
    balance: Decimal
    total_recharge: Decimal
    total_consumption: Decimal
    status: str
    activated_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CardRechargeRequest(BaseModel):
    """会员卡充值请求Schema"""
    amount: Decimal = Field(..., gt=0, description="充值金额")
    payment_method: Optional[str] = Field(None, max_length=50, description="支付方式")
    remark: Optional[str] = Field(None, max_length=255, description="备注")


class CardRechargeRecordResponse(BaseModel):
    """充值记录响应Schema"""
    id: int
    member_card_id: int
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    payment_method: Optional[str]
    transaction_no: Optional[str]
    operator_id: Optional[int]
    remark: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ 扩展用户 Schema ============

class UserWithMember(BaseModel):
    """包含会员信息的用户Schema"""
    id: int
    username: str
    mobile: Optional[str]
    email: Optional[str]
    role: str
    points: int
    total_points: int
    member_level_id: Optional[int]
    member_level: Optional[MemberLevelResponse]
    member_card: Optional[MemberCardResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
