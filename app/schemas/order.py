"""
订单 Schema

定义订单相关的请求和响应数据模型。
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    """创建订单项"""
    product_id: int = Field(..., description="商品ID")
    quantity: int = Field(..., gt=0, description="购买数量")


class OrderItemResponse(BaseModel):
    """订单项响应"""
    id: int
    order_id: int
    product_id: Optional[int] = None
    product_name: str
    product_price: Decimal
    quantity: int
    subtotal: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """创建订单"""
    items: List[OrderItemCreate] = Field(..., min_length=1, description="订单商品列表")
    remark: Optional[str] = Field(None, max_length=500, description="订单备注")


class OrderUpdate(BaseModel):
    """更新订单"""
    status: Optional[str] = Field(None, description="订单状态")
    remark: Optional[str] = Field(None, max_length=500, description="订单备注")


class OrderCancelRequest(BaseModel):
    """订单取消请求"""
    reason: Optional[str] = Field(None, max_length=200, description="取消原因")


class OrderCancelResponse(BaseModel):
    """订单取消响应"""
    success: bool
    message: str
    refund_amount: Optional[str] = None
    points_revoked: int = 0


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    order_no: str
    user_id: int
    payment_id: Optional[int] = None
    original_amount: Optional[Decimal] = None
    points_used: Optional[int] = None
    points_discount: Optional[Decimal] = None
    member_discount: Optional[Decimal] = None
    total_amount: Decimal
    paid_amount: Optional[Decimal] = None  # 实际支付金额（从payment.amount获取）
    status: str
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderWithItems(OrderResponse):
    """订单及明细"""
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True

