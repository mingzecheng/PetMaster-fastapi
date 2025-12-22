"""
订单模型

定义商品订单的数据结构，包括订单主表和订单明细表。
"""
from sqlalchemy import Column, BigInteger, String, DECIMAL, Integer, TIMESTAMP, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class OrderStatus(str, enum.Enum):
    """订单状态枚举"""
    PENDING = "pending"      # 待支付
    PAID = "paid"           # 已支付
    CANCELLED = "cancelled" # 已取消
    COMPLETED = "completed" # 已完成
    REFUNDED = "refunded"   # 已退款


class Order(Base):
    """订单主表模型"""
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='订单ID')
    order_no = Column(String(50), unique=True, nullable=False, index=True, comment='订单编号')
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, comment='用户ID')
    payment_id = Column(BigInteger, ForeignKey('payments.id', ondelete='SET NULL'), comment='支付记录ID')
    
    # 金额相关字段
    original_amount = Column(DECIMAL(10, 2), comment='原始金额（未抵扣前）')
    points_used = Column(Integer, default=0, comment='使用的积分数量')
    points_discount = Column(DECIMAL(10, 2), default=0, comment='积分抵扣金额')
    member_discount = Column(DECIMAL(10, 2), default=0, comment='会员折扣金额')
    total_amount = Column(DECIMAL(10, 2), nullable=False, comment='订单总金额（实际支付）')
    
    status = Column(String(20), default='pending', comment='订单状态: pending/paid/cancelled/completed/refunded')
    remark = Column(Text, comment='订单备注')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    paid_at = Column(TIMESTAMP, comment='支付时间')
    completed_at = Column(TIMESTAMP, comment='完成时间')

    # 关系
    user = relationship("User", back_populates="orders")
    payment = relationship("Payment", back_populates="order")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, order_no={self.order_no}, total_amount={self.total_amount}, status={self.status})>"


class OrderItem(Base):
    """订单明细表模型"""
    __tablename__ = "order_items"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='明细ID')
    order_id = Column(BigInteger, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True, comment='订单ID')
    product_id = Column(BigInteger, ForeignKey('products.id', ondelete='SET NULL'), comment='商品ID')
    product_name = Column(String(100), nullable=False, comment='商品名称（快照）')
    product_price = Column(DECIMAL(10, 2), nullable=False, comment='商品价格（快照）')
    quantity = Column(Integer, nullable=False, comment='购买数量')
    subtotal = Column(DECIMAL(10, 2), nullable=False, comment='小计金额')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')

    # 关系
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, product_name={self.product_name}, quantity={self.quantity}, subtotal={self.subtotal})>"
