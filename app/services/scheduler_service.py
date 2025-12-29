"""
订单超时自动取消服务

定时检查并取消超时未支付的订单,恢复商品库存。
"""

from datetime import datetime, timedelta
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.order import Order, OrderStatus, OrderItem
from app.models.product import Product
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OrderSchedulerService:
    """
    订单定时任务服务
    
    负责自动取消超时未支付的订单并恢复库存。
    """
    
    def __init__(self):
        """初始化调度器"""
        self.scheduler = BackgroundScheduler()
        self.timeout_minutes = 30  # 订单超时时间(分钟)
        self.check_interval_minutes = 5  # 检查间隔(分钟)
        
    def start(self):
        """启动调度器"""
        try:
            # 添加定时任务:每5分钟检查一次超时订单
            self.scheduler.add_job(
                func=self._cancel_expired_orders,
                trigger=IntervalTrigger(minutes=self.check_interval_minutes),
                id='cancel_expired_orders',
                name='取消超时未支付订单',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info(f"订单调度器已启动 - 超时时间:{self.timeout_minutes}分钟, 检查间隔:{self.check_interval_minutes}分钟")
            
        except Exception as e:
            logger.error(f"订单调度器启动失败: {str(e)}")
            raise
    
    def shutdown(self):
        """关闭调度器"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                logger.info("订单调度器已关闭")
        except Exception as e:
            logger.error(f"订单调度器关闭失败: {str(e)}")
    
    def _cancel_expired_orders(self):
        """
        取消超时未支付的订单
        
        核心逻辑:
        1. 查询超过30分钟仍未支付的订单
        2. 批量更新订单状态为cancelled
        3. 恢复商品库存
        4. 记录日志
        """
        db: Session = SessionLocal()
        try:
            # 计算超时时间点
            timeout_time = datetime.now() - timedelta(minutes=self.timeout_minutes)
            
            # 查询超时的待支付订单
            expired_orders = db.query(Order).filter(
                and_(
                    Order.status == OrderStatus.PENDING.value,
                    Order.created_at <= timeout_time
                )
            ).limit(100).all()  # 每次最多处理100个订单
            
            if not expired_orders:
                logger.debug("未发现超时订单")
                return
            
            logger.info(f"发现 {len(expired_orders)} 个超时订单,开始自动取消...")
            
            cancelled_count = 0
            for order in expired_orders:
                try:
                    # 恢复订单中商品的库存
                    self._restore_order_stock(db, order)
                    
                    # 更新订单状态
                    order.status = OrderStatus.CANCELLED.value
                    order.remark = f"系统自动取消: 超时未支付(超时{self.timeout_minutes}分钟)"
                    order.updated_at = datetime.now()
                    
                    db.add(order)
                    cancelled_count += 1
                    
                    logger.info(f"订单已自动取消: order_id={order.id}, order_no={order.order_no}")
                    
                except Exception as e:
                    logger.error(f"取消订单失败: order_id={order.id}, error={str(e)}")
                    db.rollback()
                    continue
            
            # 提交所有更改
            db.commit()
            
            logger.info(f"订单自动取消完成: 成功取消 {cancelled_count}/{len(expired_orders)} 个订单")
            
        except Exception as e:
            logger.error(f"取消超时订单异常: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def _restore_order_stock(self, db: Session, order: Order):
        """
        恢复订单占用的商品库存
        
        Args:
            db: 数据库会话
            order: 订单对象
        """
        try:
            # 获取订单所有商品
            order_items = db.query(OrderItem).filter(
                OrderItem.order_id == order.id
            ).all()
            
            for item in order_items:
                if item.product_id:
                    # 查询商品并恢复库存
                    product = db.query(Product).filter(
                        Product.id == item.product_id
                    ).first()
                    
                    if product:
                        old_stock = product.stock
                        product.stock += item.quantity
                        db.add(product)
                        
                        logger.debug(
                            f"库存已恢复: product_id={product.id}, "
                            f"product_name={product.name}, "
                            f"quantity={item.quantity}, "
                            f"stock: {old_stock} -> {product.stock}"
                        )
                    else:
                        logger.warning(f"商品不存在,无法恢复库存: product_id={item.product_id}")
                        
        except Exception as e:
            logger.error(f"恢复订单库存失败: order_id={order.id}, error={str(e)}")
            raise


# 创建全局调度器实例
order_scheduler = OrderSchedulerService()
