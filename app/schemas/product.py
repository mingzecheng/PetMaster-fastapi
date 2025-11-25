from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ProductBase(BaseModel):
    """商品基础Schema"""
    name: str = Field(..., max_length=100, description="商品名称")
    category: Optional[str] = Field(None, max_length=50, description="商品分类")
    price: Decimal = Field(..., ge=0, description="商品价格")
    stock: int = Field(default=0, ge=0, description="库存数量")


class ProductCreate(ProductBase):
    """商品创建Schema"""
    pass


class ProductUpdate(BaseModel):
    """商品更新Schema"""
    name: Optional[str] = Field(None, max_length=100, description="商品名称")
    category: Optional[str] = Field(None, max_length=50, description="商品分类")
    price: Optional[Decimal] = Field(None, ge=0, description="商品价格")
    stock: Optional[int] = Field(None, ge=0, description="库存数量")


class ProductResponse(ProductBase):
    """商品响应Schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
