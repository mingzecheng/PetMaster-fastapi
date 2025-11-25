from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.payment import PaymentStatus, PaymentMethod


class PaymentBase(BaseModel):
    """支付基础Schema"""
    out_trade_no: str = Field(..., max_length=64, description="商户订单号")
    amount: str = Field(..., description="支付金额")
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, description="支付状态")
    method: PaymentMethod = Field(..., description="支付方式")
    subject: str = Field(..., max_length=255, description="商品标题")
    description: Optional[str] = Field(None, description="商品描述")
    related_id: Optional[int] = Field(None, description="关联ID")
    related_type: Optional[str] = Field(None, max_length=32, description="关联类型")

    @field_validator('amount', mode='before')
    @classmethod
    def convert_amount_to_str(cls, v):
        """将Decimal类型的金额转换为字符串"""
        if isinstance(v, Decimal):
            return str(v)
        return v


class PaymentCreate(BaseModel):
    """支付创建Schema"""
    amount: str = Field(..., description="支付金额")
    subject: str = Field(..., max_length=255, description="商品标题")
    description: Optional[str] = Field(None, description="商品描述")
    method: PaymentMethod = Field(default=PaymentMethod.ALIPAY, description="支付方式")
    related_id: Optional[int] = Field(None, description="关联ID")
    related_type: Optional[str] = Field(None, max_length=32, description="关联类型")


class PaymentUpdate(BaseModel):
    """支付更新Schema"""
    status: Optional[PaymentStatus] = Field(None, description="支付状态")
    trade_no: Optional[str] = Field(None, max_length=64, description="第三方交易号")
    response_data: Optional[str] = Field(None, description="支付宝返回数据")
    notify_data: Optional[str] = Field(None, description="异步通知数据")
    error_message: Optional[str] = Field(None, description="错误信息")


class PaymentResponse(PaymentBase):
    """支付响应Schema"""
    id: int
    user_id: int
    trade_no: Optional[str]
    response_data: Optional[str]
    notify_data: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    paid_at: Optional[datetime]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, decimal_as_str=True)


class PaymentRequestResponse(BaseModel):
    """支付请求响应Schema"""
    payment_id: int = Field(..., description="支付记录ID")
    out_trade_no: str = Field(..., description="商户订单号")
    amount: str = Field(..., description="支付金额")
    subject: str = Field(..., description="商品标题")
    qr_code: Optional[str] = Field(None, description="二维码链接（支付宝）")
    pay_url: Optional[str] = Field(None, description="支付链接")
    status: str = Field(..., description="支付状态")
    message: str = Field(..., description="提示信息")
