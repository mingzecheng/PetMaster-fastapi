"""
订单服务模块

处理订单创建、取消和退款逻辑。
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
import time
import random

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus, OrderItem
from app.models.payment import Payment, PaymentStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.boarding import Boarding, BoardingStatus
from app.models.member import PointRecord
from app.models.user import User
from app.models.product import Product
from app.schemas.order import OrderItemCreate
from app.utils.logger import get_logger
from app.utils.exceptions import AppException

logger = get_logger(__name__)


class OrderCreationService:
    """
    订单创建服务
    
    提供商品订单创建功能。
    """
    
    @staticmethod
    def create_product_order(
        db: Session,
        user_id: int,
        items: List[OrderItemCreate],
        remark: str = None
    ) -> Order:
        """
        创建商品订单
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            items: 订单商品列表
            remark: 订单备注
            
        Returns:
            Order 创建的订单对象
            
        Raises:
            AppException: 创建失败时抛出异常
        """
        try:
            # 1. 查询用户并获取会员折扣
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise AppException("用户不存在")
            
            # 获取会员折扣率（默认1.0表示无折扣）
            member_discount_rate = 1.0
            if user.member_level and hasattr(user.member_level, 'discount_rate'):
                member_discount_rate = float(user.member_level.discount_rate) if user.member_level.discount_rate else 1.0
            
            # 2. 验证商品并计算金额
            order_items_to_create = []
            original_amount = Decimal('0')
            total_amount = Decimal('0')
            
            for item in items:
                # 查询商品
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if not product:
                    raise AppException(f"商品不存在: product_id={item.product_id}")
                
                # 验证库存
                if product.stock < item.quantity:
                    raise AppException(f"商品 {product.name} 库存不足，当前库存: {product.stock}")
                
                # 计算价格
                unit_price = Decimal(str(product.price))
                item_subtotal = unit_price * item.quantity
                original_amount += item_subtotal
                
                # 应用会员折扣
                discounted_subtotal = item_subtotal * Decimal(str(member_discount_rate))
                total_amount += discounted_subtotal
                
                # 准备OrderItem数据
                order_items_to_create.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_price': unit_price,
                    'quantity': item.quantity,
                    'subtotal': discounted_subtotal  # 存储折后价
                })
                
            # 计算会员折扣金额
            member_discount = original_amount - total_amount
            
            # 3. 生成唯一订单号
            order_no = f"ORD{int(time.time())}{random.randint(1000, 9999)}"
            
            # 4. 创建订单
            order = Order(
                order_no=order_no,
                user_id=user_id,
                original_amount=original_amount,
                member_discount=member_discount,
                total_amount=total_amount,
                status=OrderStatus.PENDING.value,
                remark=remark
            )
            db.add(order)
            db.flush()  # 获取order.id
            
            # 5. 创建订单明细
            for item_data in order_items_to_create:
                order_item = OrderItem(
                    order_id=order.id,
                    **item_data
                )
                db.add(order_item)
            
            # 6. 扣减库存
            for item in items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                product.stock -= item.quantity
                db.add(product)
            
            db.commit()
            db.refresh(order)
            
            logger.info(f"订单创建成功: order_id={order.id}, order_no={order_no}, total_amount={total_amount}")
            return order
            
        except AppException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"创建订单异常: {str(e)}")
            raise AppException(f"创建订单失败: {str(e)}")


class CancelResult:

    """取消操作结果"""

    def __init__(
        self,
        success: bool,
        message: str = None,
        refund_amount: Decimal = None,
        points_revoked: int = 0
    ):
        self.success = success
        self.message = message
        self.refund_amount = refund_amount
        self.points_revoked = points_revoked

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "message": self.message,
            "refund_amount": str(self.refund_amount) if self.refund_amount else None,
            "points_revoked": self.points_revoked
        }


class OrderCancelService:
    """
    订单取消服务

    提供订单、预约、寄养的取消和退款功能。
    """

    @staticmethod
    def cancel_order(
        db: Session,
        order_id: int,
        user_id: int,
        reason: str = None
    ) -> CancelResult:
        """
        取消订单

        根据订单状态执行不同的取消逻辑：
        - pending（待支付）：直接取消
        - paid（已支付）：退款
        - completed（已完成）：退款 + 回收积分

        Args:
            db: 数据库会话
            order_id: 订单ID
            user_id: 用户ID
            reason: 取消原因

        Returns:
            CancelResult 取消结果
        """
        try:
            # 查询订单
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return CancelResult(success=False, message="订单不存在")

            # 权限检查
            if order.user_id != user_id:
                return CancelResult(success=False, message="无权取消此订单")

            # 检查订单状态
            if order.status == OrderStatus.CANCELLED.value:
                return CancelResult(success=False, message="订单已取消")
            if order.status == OrderStatus.REFUNDED.value:
                return CancelResult(success=False, message="订单已退款")

            refund_amount = None
            points_revoked = 0

            # 根据状态执行不同逻辑
            if order.status == OrderStatus.PENDING.value:
                # 待支付：直接取消
                order.status = OrderStatus.CANCELLED.value
                order.remark = f"用户取消: {reason or '无'}"
                logger.info(f"订单取消（待支付）: order_id={order_id}")

            elif order.status == OrderStatus.PAID.value:
                # 已支付：需要退款
                if order.payment_id:
                    refund_result = OrderCancelService._process_refund(db, order.payment_id)
                    if not refund_result:
                        return CancelResult(success=False, message="退款处理失败")
                    refund_amount = order.total_amount

                order.status = OrderStatus.REFUNDED.value
                order.remark = f"用户取消退款: {reason or '无'}"
                logger.info(f"订单取消（已支付）: order_id={order_id}, refund={refund_amount}")

            elif order.status == OrderStatus.COMPLETED.value:
                # 已完成：退款 + 回收积分
                if order.payment_id:
                    refund_result = OrderCancelService._process_refund(db, order.payment_id)
                    if not refund_result:
                        return CancelResult(success=False, message="退款处理失败")
                    refund_amount = order.total_amount

                # 回收消费获得的积分
                points_revoked = OrderCancelService._revoke_points(db, order.user_id, order)

                order.status = OrderStatus.REFUNDED.value
                order.remark = f"消费后取消退款: {reason or '无'}, 回收积分: {points_revoked}"
                logger.info(f"订单取消（已完成）: order_id={order_id}, refund={refund_amount}, points_revoked={points_revoked}")

            else:
                return CancelResult(success=False, message=f"订单状态 {order.status} 不支持取消")

            db.add(order)
            db.commit()

            return CancelResult(
                success=True,
                message="订单取消成功",
                refund_amount=refund_amount,
                points_revoked=points_revoked
            )

        except Exception as e:
            logger.error(f"取消订单异常: {str(e)}")
            db.rollback()
            return CancelResult(success=False, message=f"取消失败: {str(e)}")

    @staticmethod
    def cancel_appointment(
        db: Session,
        appointment_id: int,
        user_id: int,
        reason: str = None
    ) -> CancelResult:
        """
        取消预约

        根据预约状态执行不同的取消逻辑：
        - pending（待支付）：直接取消
        - confirmed（已支付）：退款

        Args:
            db: 数据库会话
            appointment_id: 预约ID
            user_id: 用户ID
            reason: 取消原因

        Returns:
            CancelResult 取消结果
        """
        try:
            # 查询预约
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            if not appointment:
                return CancelResult(success=False, message="预约不存在")

            # 权限检查（通过宠物的owner_id）
            from app.models.pet import Pet
            pet = db.query(Pet).filter(Pet.id == appointment.pet_id).first()
            if not pet or pet.owner_id != user_id:
                return CancelResult(success=False, message="无权取消此预约")

            # 检查状态
            if appointment.status == AppointmentStatus.CANCELLED:
                return CancelResult(success=False, message="预约已取消")
            if appointment.status == AppointmentStatus.REFUNDED:
                return CancelResult(success=False, message="预约已退款")
            if appointment.status == AppointmentStatus.COMPLETED:
                return CancelResult(success=False, message="已完成的预约不可取消")

            refund_amount = None

            if appointment.status == AppointmentStatus.PENDING:
                # 待支付：直接取消
                appointment.status = AppointmentStatus.CANCELLED
                appointment.cancel_reason = reason
                logger.info(f"预约取消（待支付）: appointment_id={appointment_id}")

            elif appointment.status == AppointmentStatus.CONFIRMED:
                # 已支付：退款
                if appointment.payment_id:
                    refund_result = OrderCancelService._process_refund(db, appointment.payment_id)
                    if not refund_result:
                        return CancelResult(success=False, message="退款处理失败")
                    refund_amount = appointment.price

                appointment.status = AppointmentStatus.REFUNDED
                appointment.cancel_reason = reason
                logger.info(f"预约取消（已支付）: appointment_id={appointment_id}, refund={refund_amount}")

            else:
                return CancelResult(success=False, message=f"预约状态 {appointment.status} 不支持取消")

            db.add(appointment)
            db.commit()

            return CancelResult(
                success=True,
                message="预约取消成功",
                refund_amount=refund_amount
            )

        except Exception as e:
            logger.error(f"取消预约异常: {str(e)}")
            db.rollback()
            return CancelResult(success=False, message=f"取消失败: {str(e)}")

    @staticmethod
    def cancel_boarding(
        db: Session,
        boarding_id: int,
        user_id: int,
        reason: str = None
    ) -> CancelResult:
        """
        取消寄养

        根据寄养状态执行不同的取消逻辑：
        - pending（待支付）：直接取消
        - active（进行中/已支付）：退款

        Args:
            db: 数据库会话
            boarding_id: 寄养ID
            user_id: 用户ID
            reason: 取消原因

        Returns:
            CancelResult 取消结果
        """
        try:
            # 查询寄养
            boarding = db.query(Boarding).filter(Boarding.id == boarding_id).first()
            if not boarding:
                return CancelResult(success=False, message="寄养记录不存在")

            # 权限检查（通过宠物的owner_id）
            from app.models.pet import Pet
            pet = db.query(Pet).filter(Pet.id == boarding.pet_id).first()
            if not pet or pet.owner_id != user_id:
                return CancelResult(success=False, message="无权取消此寄养")

            # 检查状态
            if boarding.status == BoardingStatus.CANCELLED:
                return CancelResult(success=False, message="寄养已取消")
            if boarding.status == BoardingStatus.REFUNDED:
                return CancelResult(success=False, message="寄养已退款")
            if boarding.status == BoardingStatus.COMPLETED:
                return CancelResult(success=False, message="已完成的寄养不可取消")

            refund_amount = None

            if boarding.status == BoardingStatus.PENDING:
                # 待支付：直接取消
                boarding.status = BoardingStatus.CANCELLED
                boarding.cancel_reason = reason
                logger.info(f"寄养取消（待支付）: boarding_id={boarding_id}")

            elif boarding.status == BoardingStatus.ACTIVE:
                # 进行中/已支付：退款
                if boarding.payment_id:
                    refund_result = OrderCancelService._process_refund(db, boarding.payment_id)
                    if not refund_result:
                        return CancelResult(success=False, message="退款处理失败")
                    refund_amount = boarding.total_cost

                boarding.status = BoardingStatus.REFUNDED
                boarding.cancel_reason = reason
                logger.info(f"寄养取消（进行中）: boarding_id={boarding_id}, refund={refund_amount}")

            else:
                return CancelResult(success=False, message=f"寄养状态 {boarding.status} 不支持取消")

            db.add(boarding)
            db.commit()

            return CancelResult(
                success=True,
                message="寄养取消成功",
                refund_amount=refund_amount
            )

        except Exception as e:
            logger.error(f"取消寄养异常: {str(e)}")
            db.rollback()
            return CancelResult(success=False, message=f"取消失败: {str(e)}")

    @staticmethod
    def _process_refund(db: Session, payment_id: int) -> bool:
        """
        处理退款（Mock模式下直接更新状态）

        Args:
            db: 数据库会话
            payment_id: 支付记录ID

        Returns:
            是否成功
        """
        try:
            payment = db.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                logger.error(f"退款失败：支付记录不存在 payment_id={payment_id}")
                return False

            if payment.status != PaymentStatus.PAID:
                logger.error(f"退款失败：支付状态异常 status={payment.status}")
                return False

            # Mock模式：直接更新状态为已退款
            payment.status = PaymentStatus.REFUNDED
            payment.notify_data = f"Mock退款 - {datetime.now().isoformat()}"
            db.add(payment)

            logger.info(f"[Mock退款] 退款成功: payment_id={payment_id}, amount={payment.amount}")
            return True

        except Exception as e:
            logger.error(f"处理退款异常: {str(e)}")
            return False

    @staticmethod
    def _revoke_points(db: Session, user_id: int, order: Order) -> int:
        """
        回收消费积分

        Args:
            db: 数据库会话
            user_id: 用户ID
            order: 订单对象

        Returns:
            回收的积分数量
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"回收积分失败：用户不存在 user_id={user_id}")
                return 0

            # 计算应回收的积分（实际支付金额 = 积分数）
            points_to_revoke = int(float(order.total_amount))
            if points_to_revoke <= 0:
                return 0

            # 检查用户积分是否足够
            if user.points < points_to_revoke:
                points_to_revoke = user.points  # 最多扣除当前积分

            # 扣除积分
            old_balance = user.points
            user.points -= points_to_revoke
            new_balance = user.points

            # 创建积分记录
            point_record = PointRecord(
                user_id=user_id,
                points=-points_to_revoke,
                balance=new_balance,
                type='revoke',
                reason=f'订单取消回收积分 (订单号:{order.order_no})'
            )
            db.add(user)
            db.add(point_record)

            logger.info(f"积分回收成功: user_id={user_id}, points_revoked={points_to_revoke}, balance={new_balance}")
            return points_to_revoke

        except Exception as e:
            logger.error(f"回收积分异常: {str(e)}")
            return 0


# 创建全局服务实例
order_cancel_service = OrderCancelService()
