"""
订单 CRUD 操作
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderItemCreate
from app.crud.base import CRUDBase


class CRUDOrder(CRUDBase[Order, None, None]):
    """订单CRUD操作"""
    
    def get_by_order_no(self, db: Session, *, order_no: str) -> Optional[Order]:
        """
        通过订单编号获取订单
        
        Args:
            db: 数据库会话
            order_no: 订单编号
            
        Returns:
            订单对象，不存在返回 None
        """
        return db.query(Order).filter(Order.order_no == order_no).first()
    
    def get_by_user(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Order]:
        """
        获取用户的订单列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            skip: 跳过数量
            limit: 返回数量
            
        Returns:
            订单列表
        """
        return (
            db.query(Order)
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_payment(self, db: Session, *, payment_id: int) -> Optional[Order]:
        """
        通过支付ID获取订单
        
        Args:
            db: 数据库会话
            payment_id: 支付ID
            
        Returns:
            订单对象，不存在返回 None
        """
        return db.query(Order).filter(Order.payment_id == payment_id).first()
    
    def create_with_items(
        self,
        db: Session,
        *,
        order_no: str,
        user_id: int,
        items: List[OrderItemCreate],
        payment_id: Optional[int] = None,
        remark: Optional[str] = None
    ) -> Optional[Order]:
        """
        创建订单及明细
        
        Args:
            db: 数据库会话
            order_no: 订单编号
            user_id: 用户ID
            items: 订单商品列表
            payment_id: 支付ID
            remark: 订单备注
            
        Returns:
            创建的订单对象，失败返回 None
        """
        try:
            # 计算总金额并验证商品
            total_amount = Decimal('0.00')
            order_items_data = []
            
            for item in items:
                # 获取商品信息
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if not product:
                    raise ValueError(f"商品不存在: product_id={item.product_id}")
                
                # 检查库存
                if product.stock < item.quantity:
                    raise ValueError(f"商品库存不足: {product.name}，当前库存={product.stock}")
                
                # 计算小计
                subtotal = product.price * item.quantity
                total_amount += subtotal
                
                # 保存订单明细数据
                order_items_data.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "product_price": product.price,
                    "quantity": item.quantity,
                    "subtotal": subtotal
                })
            
            # 创建订单
            order = Order(
                order_no=order_no,
                user_id=user_id,
                payment_id=payment_id,
                total_amount=total_amount,
                status=OrderStatus.PENDING.value,
                remark=remark
            )
            db.add(order)
            db.flush()  # 获取订单ID
            
            # 创建订单明细
            for item_data in order_items_data:
                order_item = OrderItem(
                    order_id=order.id,
                    **item_data
                )
                db.add(order_item)
            
            db.commit()
            db.refresh(order)
            
            return order
            
        except Exception as e:
            db.rollback()
            raise e
    
    def update_status(
        self,
        db: Session,
        *,
        order_id: int,
        status: str
    ) -> Optional[Order]:
        """
        更新订单状态
        
        Args:
            db: 数据库会话
            order_id: 订单ID
            status: 新状态
            
        Returns:
            更新后的订单对象，不存在返回 None
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None
        
        order.status = status
        
        # 如果是已支付状态，设置支付时间
        if status == OrderStatus.PAID.value and not order.paid_at:
            from datetime import datetime
            order.paid_at = datetime.now()
        
        # 如果是已完成状态，设置完成时间
        if status == OrderStatus.COMPLETED.value and not order.completed_at:
            from datetime import datetime
            order.completed_at = datetime.now()
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        return order


# 创建CRUD实例
crud_order = CRUDOrder(Order)
