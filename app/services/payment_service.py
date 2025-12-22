"""
统一支付服务模块

封装支付创建、状态查询、回调处理等逻辑，
支持支付宝支付，预留微信支付扩展接口。
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.member import MemberCard, CardRechargeRecord
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


class PaymentResult:
    """支付创建结果"""

    def __init__(
        self,
        success: bool,
        payment_id: int = None,
        out_trade_no: str = None,
        pay_url: str = None,
        qr_code: str = None,
        message: str = None,
        error: str = None
    ):
        self.success = success
        self.payment_id = payment_id
        self.out_trade_no = out_trade_no
        self.pay_url = pay_url
        self.qr_code = qr_code
        self.message = message
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "payment_id": self.payment_id,
            "out_trade_no": self.out_trade_no,
            "pay_url": self.pay_url,
            "qr_code": self.qr_code,
            "message": self.message,
            "error": self.error
        }


class PaymentService:
    """
    统一支付服务

    提供支付创建、状态查询、回调处理等功能。
    当前支持支付宝，预留微信支付扩展接口。
    """

    @staticmethod
    def generate_trade_no(prefix: str, user_id: int) -> str:
        """
        生成商户订单号

        Args:
            prefix: 订单号前缀（如 PET、CARD）
            user_id: 用户ID

        Returns:
            格式化的订单号
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = uuid.uuid4().hex[:8]
        return f"{prefix}_{user_id}_{timestamp}_{random_suffix}"

    @staticmethod
    def create_alipay_payment(
        db: Session,
        user_id: int,
        amount: Decimal,
        subject: str,
        description: str = None,
        related_id: int = None,
        related_type: str = None,
        return_url: str = None,
        notify_url: str = None
    ) -> PaymentResult:
        """
        创建支付订单（Mock模式）

        Args:
            db: 数据库会话
            user_id: 用户ID
            amount: 支付金额
            subject: 商品标题
            description: 商品描述
            related_id: 关联ID（如会员卡ID、商品ID）
            related_type: 关联类型（如 member_card_recharge、product）
            return_url: 支付完成后跳转地址
            notify_url: 异步通知地址

        Returns:
            PaymentResult 支付创建结果
        """
        # 生成订单号
        out_trade_no = PaymentService.generate_trade_no("PAY", user_id)

        logger.info(f"创建Mock支付: user_id={user_id}, amount={amount}, out_trade_no={out_trade_no}")

        try:
            # 创建支付记录
            payment = Payment(
                user_id=user_id,
                out_trade_no=out_trade_no,
                amount=amount,
                status=PaymentStatus.PENDING,
                method=PaymentMethod.ALIPAY,
                subject=subject,
                description=description,
                related_id=related_id,
                related_type=related_type
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)

            logger.info(f"支付记录创建成功: payment_id={payment.id}")

            # Mock支付模式：直接返回模拟支付URL
            logger.info("[Mock支付] 使用模拟支付模式")
            
            mock_pay_url = f"http://localhost:5173/pages/payment/mock?out_trade_no={out_trade_no}"
            
            payment.response_data = str({
                "pay_url": mock_pay_url,
                "code": "MOCK",
                "msg": "模拟支付"
            })
            db.add(payment)
            db.commit()
            
            logger.info(f"[Mock支付] 支付请求创建成功: {out_trade_no}")
            
            return PaymentResult(
                success=True,
                payment_id=payment.id,
                out_trade_no=out_trade_no,
                pay_url=mock_pay_url,
                message="[模拟支付] 支付请求已生成"
            )

        except Exception as e:
            logger.error(f"创建支付异常: {str(e)}")
            db.rollback()
            return PaymentResult(
                success=False,
                error=str(e)
            )

    @staticmethod
    def query_payment_status(
        db: Session,
        out_trade_no: str,
        sync_from_alipay: bool = True
    ) -> Optional[Payment]:
        """
        查询支付状态（Mock模式下仅查询数据库）

        Args:
            db: 数据库会话
            out_trade_no: 商户订单号
            sync_from_alipay: 是否从支付宝同步最新状态（Mock模式下被忽略）

        Returns:
            支付记录，不存在返回 None
        """
        payment = db.query(Payment).filter(Payment.out_trade_no == out_trade_no).first()
        
        if payment:
            logger.info(f"[Mock支付] 查询支付状态: {out_trade_no} -> {payment.status}")

        return payment

    @staticmethod
    def handle_alipay_callback(
        db: Session,
        data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        处理支付宝异步通知（Mock模式下不使用）

        Args:
            db: 数据库会话
            data: 通知数据

        Returns:
            处理结果
        """
        logger.warning("[Mock支付] Mock模式下不支持支付宝回调，请使用Mock支付确认接口")
        return {"code": "FAIL", "message": "Mock模式不支持支付宝回调"}

    @staticmethod
    def _process_payment_success(db: Session, payment: Payment) -> bool:
        """
        处理支付成功后的业务逻辑

        根据 related_type 执行不同的业务处理：
        - member_card_recharge: 更新会员卡余额
        - product: 创建订单记录等

        Args:
            db: 数据库会话
            payment: 支付记录

        Returns:
            处理是否成功
        """
        try:
            related_type = payment.related_type

            if related_type == "member_card_recharge":
                return PaymentService._process_member_card_recharge(db, payment)
            elif related_type == "product":
                return PaymentService._process_product_purchase(db, payment)
            else:
                logger.warning(f"未知的关联类型: {related_type}")
                return True

        except Exception as e:
            logger.error(f"处理支付成功业务异常: {str(e)}")
            return False

    @staticmethod
    def _process_product_purchase(db: Session, payment: Payment) -> bool:
        """
        处理商品购买
        
        Args:
            db: 数据库会话
            payment: 支付记录
            
        Returns:
            处理是否成功
        """
        try:
            from app.models.order import Order, OrderStatus
            from app.crud.crud_product import crud_product
            import json
            
            # 从支付描述中解析商品信息
            # 格式: {"product_id": 1, "quantity": 2, "points_used": 100, "points_discount": 1.0}
            product_info = None
            if payment.description:
                try:
                    # 尝试从description中解析JSON
                    product_info = json.loads(payment.description)
                except:
                    # 如果不是JSON，尝试从related_id获取商品信息
                    if payment.related_id:
                        product_info = {"product_id": payment.related_id, "quantity": 1}
            
            if not product_info or 'product_id' not in product_info:
                logger.error(f"商品购买信息不完整: payment_id={payment.id}")
                return False
            
            product_id = product_info.get('product_id')
            quantity = product_info.get('quantity', 1)
            points_used = product_info.get('points_used', 0)
            points_discount = product_info.get('points_discount', 0.0)
            
            # 从数据库查询用户的会员等级折扣率（不依赖前端传递）
            from app.models.user import User
            from app.models.member import MemberLevel
            
            user = db.query(User).filter(User.id == payment.user_id).first()
            member_discount_rate = 1.0  # 默认无折扣
            member_level_name = ''
            
            if user and user.member_level:
                discount_rate = float(user.member_level.discount_rate or 1.0)
                if discount_rate < 1.0:
                    member_discount_rate = discount_rate
                    member_level_name = user.member_level.name
            
            logger.info(f"[商品购买] 解析信息: product_id={product_id}, quantity={quantity}, "
                       f"points_used={points_used}, points_discount={points_discount}, "
                       f"member_discount_rate={member_discount_rate}, member_level={member_level_name}")
            logger.info(f"[商品购买] payment描述: {payment.description}")
            
            # 检查是否已经创建订单（防止重复处理）
            existing_order = db.query(Order).filter(Order.payment_id == payment.id).first()
            if existing_order:
                logger.info(f"订单已存在，跳过处理: payment_id={payment.id}, order_id={existing_order.id}")
                return True
            
            # 处理积分抵扣
            if points_used > 0:
                try:
                    from app.models.member import PointRecord
                    from app.models.user import User
                    
                    # 获取用户
                    user = db.query(User).filter(User.id == payment.user_id).first()
                    if not user:
                        logger.error(f"用户不存在: user_id={payment.user_id}")
                        return False
                    
                    # 检查积分是否足够
                    if user.points < points_used:
                        logger.error(f"用户积分不足: user_id={payment.user_id}, 需要={points_used}, 当前={user.points}")
                        return False
                    
                    # 扣除积分
                    old_balance = user.points
                    user.points -= points_used
                    new_balance = user.points
                    
                    # 创建积分使用记录
                    point_record = PointRecord(
                        user_id=payment.user_id,
                        points=-points_used,  # 负数表示扣除
                        balance=new_balance,
                        type='use',
                        reason=f'订单积分抵扣 (支付单号:{payment.out_trade_no})'
                    )
                    
                    db.add(user)
                    db.add(point_record)
                    db.flush()  # 立即执行，确保积分已扣除
                    
                    logger.info(f"积分抵扣成功: user_id={payment.user_id}, points_used={points_used}, balance={new_balance}")
                    
                except Exception as e:
                    logger.error(f"积分抵扣失败: {str(e)}")
                    db.rollback()
                    return False
            
            # 生成订单号
            from datetime import datetime
            import uuid
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = uuid.uuid4().hex[:8]
            order_no = f"ORD_{payment.user_id}_{timestamp}_{random_suffix}"
            
            # 根据数据库查询的折扣率计算会员折扣金额
            # 原始金额 = 实际支付金额 / 折扣率 / (1 - 积分抵扣比例)
            # 但为了简化，我们直接用 支付金额 + 积分抵扣 + 会员折扣
            # 会员折扣金额 = (支付金额 + 积分抵扣) / 折扣率 * (1 - 折扣率)
            if member_discount_rate < 1.0:
                price_after_points = float(payment.amount) + points_discount
                original_before_member = price_after_points / member_discount_rate
                member_discount = original_before_member - price_after_points
                original_amount = original_before_member
            else:
                member_discount = 0.0
                original_amount = float(payment.amount) + points_discount
            
            logger.info(f"[商品购买] 计算金额: original={original_amount}, member_discount={member_discount}, points_discount={points_discount}, final={payment.amount}")
            
            # 使用CRUD创建订单（包含库存验证和扣减）
            from app.schemas.order import OrderItemCreate
            from app.crud.crud_order import crud_order
            
            items = [OrderItemCreate(product_id=product_id, quantity=quantity)]
            
            # 创建订单，包含积分和会员折扣信息（通过关联查询会员等级）
            order = Order(
                order_no=order_no,
                user_id=payment.user_id,
                payment_id=payment.id,
                original_amount=Decimal(str(round(original_amount, 2))),
                points_used=points_used,
                points_discount=Decimal(str(points_discount)),
                member_discount=Decimal(str(round(member_discount, 2))),
                total_amount=payment.amount,
                status=OrderStatus.PENDING.value
            )
            db.add(order)
            db.flush()  # 获取订单ID
            
            # 创建订单商品明细
            for item in items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if not product:
                    logger.error(f"商品不存在: product_id={item.product_id}")
                    db.rollback()
                    return False
                
                # 检查库存
                if product.stock < item.quantity:
                    logger.error(f"商品库存不足: {product.name}")
                    db.rollback()
                    return False
                
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name=product.name,
                    product_price=product.price,
                    quantity=item.quantity,
                    subtotal=product.price * item.quantity
                )
                db.add(order_item)
            
            
            db.flush()
            
            # 扣减库存
            product = crud_product.update_stock(db, product_id=product_id, quantity=-quantity)
            if not product:
                logger.error(f"库存扣减失败: product_id={product_id}")
                db.rollback()
                return False
            
            # 更新订单状态为已支付
            order.status = OrderStatus.PAID.value
            order.paid_at = datetime.now()
            db.add(order)
            
            # 发放消费积分（根据实际支付金额，1元=1积分）
            try:
                from app.models.member import PointRecord
                from app.models.user import User
                
                # 获取用户
                user = db.query(User).filter(User.id == payment.user_id).first()
                if user:
                    # 计算应发放的积分（实际支付金额）
                    points_to_grant = int(float(payment.amount))
                    
                    if points_to_grant > 0:
                        # 更新用户积分
                        old_balance = user.points
                        user.points += points_to_grant
                        user.total_points += points_to_grant
                        new_balance = user.points
                        
                        # 创建积分获得记录
                        point_record = PointRecord(
                            user_id=payment.user_id,
                            points=points_to_grant,
                            balance=new_balance,
                            type='earn',
                            reason=f'商品消费获得积分 (订单号:{order_no})'
                        )
                        
                        db.add(user)
                        db.add(point_record)
                        
                        logger.info(f"消费积分发放成功: user_id={payment.user_id}, points={points_to_grant}, balance={new_balance}")
                        
                        # 检查并升级会员等级
                        from app.routers.points import _check_and_upgrade_level
                        _check_and_upgrade_level(user, db)
                        
            except Exception as e:
                logger.error(f"发放消费积分失败: {str(e)}")
                # 积分发放失败不影响订单，继续处理
            
            # 提交所有更改到数据库
            db.commit()
            db.refresh(order)
            
            logger.info(
                f"商品购买成功: payment_id={payment.id}, order_id={order.id}, "
                f"product_id={product_id}, quantity={quantity}, points_used={points_used}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"处理商品购买异常: {str(e)}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            db.rollback()
            return False


    @staticmethod
    def _process_member_card_recharge(db: Session, payment: Payment) -> bool:
        """
        处理会员卡充值

        Args:
            db: 数据库会话
            payment: 支付记录

        Returns:
            处理是否成功
        """
        try:
            card_id = payment.related_id
            if not card_id:
                logger.error(f"会员卡充值缺少 card_id: payment_id={payment.id}")
                return False

            # 获取会员卡
            card = db.query(MemberCard).filter(MemberCard.id == card_id).first()
            if not card:
                logger.error(f"会员卡不存在: card_id={card_id}")
                return False

            # 记录充值前余额
            balance_before = card.balance
            balance_after = balance_before + payment.amount

            # 更新会员卡余额
            card.balance = balance_after
            card.total_recharge += payment.amount

            # 创建充值记录
            recharge_record = CardRechargeRecord(
                member_card_id=card_id,
                amount=payment.amount,
                balance_before=balance_before,
                balance_after=balance_after,
                payment_method="alipay",
                transaction_no=payment.trade_no,
                operator_id=None,  # 用户自助充值
                remark="支付宝在线充值"
            )

            db.add(card)
            db.add(recharge_record)
            db.commit()

            logger.info(
                f"会员卡充值成功: card_id={card_id}, "
                f"amount={payment.amount}, balance={balance_after}"
            )

            return True

        except Exception as e:
            logger.error(f"处理会员卡充值异常: {str(e)}")
            db.rollback()
            return False


# 创建全局服务实例
payment_service = PaymentService()
