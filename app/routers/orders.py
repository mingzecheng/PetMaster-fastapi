"""
订单管理路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.schemas.order import OrderResponse, OrderWithItems, OrderCancelRequest, OrderCancelResponse, OrderCreate
from app.crud.crud_order import crud_order
from app.utils.dependencies import get_current_active_user
from app.utils.exceptions import NotFoundError, ForbiddenError
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/orders", tags=["订单管理"])


@router.post("/", response_model=OrderWithItems, summary="创建商品订单", status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建商品订单
    
    - **items**: 订单商品列表（至少1个）
    - **remark**: 订单备注（可选）
    
    返回：
    - 创建的订单对象（包含订单明细）
    
    注意：
    - 会自动应用会员折扣
    - 订单创建后状态为pending（待支付）
    - 库存会立即扣减
    """
    logger.info(f"创建订单: user_id={current_user.id}, items_count={len(order_in.items)}")
    
    from app.services.order_service import OrderCreationService
    
    try:
        order = OrderCreationService.create_product_order(
            db=db,
            user_id=current_user.id,
            items=order_in.items,
            remark=order_in.remark
        )
        
        # 重新查询以获取关联的items
        order = crud_order.get(db, id=order.id)
        
        logger.info(f"订单创建成功: order_id={order.id}, order_no={order.order_no}")
        return order
        
    except Exception as e:
        logger.error(f"创建订单失败: {str(e)}")
        from app.utils.exceptions import AppException
        raise AppException(str(e))


@router.get("/", response_model=List[OrderResponse], summary="获取我的订单列表")
async def get_my_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户的订单列表
    
    - **skip**: 跳过数量
    - **limit**: 返回数量
    """
    logger.info(f"获取订单列表: user_id={current_user.id}")
    
    orders = crud_order.get_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    
    logger.info(f"订单列表获取成功: count={len(orders)}")
    return orders


@router.get("/{order_id}", response_model=OrderWithItems, summary="获取订单详情")
async def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取订单详情（包含订单明细）
    
    - **order_id**: 订单ID
    """
    logger.info(f"获取订单详情: order_id={order_id}, user_id={current_user.id}")
    
    order = crud_order.get(db, id=order_id)
    
    if not order:
        raise NotFoundError("订单不存在")
    
    # 权限检查：会员只能查看自己的订单
    if current_user.role.value == "member" and order.user_id != current_user.id:
        raise ForbiddenError("无权查看此订单")
    
    # 从payment表获取实际支付金额
    if order.payment_id:
        from app.models.payment import Payment
        payment = db.query(Payment).filter(Payment.id == order.payment_id).first()
        if payment:
            # 动态添加 paid_amount 属性（数据库的真实支付金额）
            order.paid_amount = payment.amount
    
    return order


@router.get("/payment/{out_trade_no}", response_model=Optional[OrderWithItems], summary="通过支付单号查询订单")
async def get_order_by_payment(
    out_trade_no: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    通过支付单号查询订单
    
    - **out_trade_no**: 支付单号
    """
    logger.info(f"通过支付单号查询订单: out_trade_no={out_trade_no}, user_id={current_user.id}")
    
    from app.models.payment import Payment
    
    # 先查询支付记录
    payment = db.query(Payment).filter(Payment.out_trade_no == out_trade_no).first()
    
    if not payment:
        raise NotFoundError("支付记录不存在")
    
    # 权限检查
    if current_user.role.value == "member" and payment.user_id != current_user.id:
        raise ForbiddenError("无权查看此支付记录")
    
    # 查询订单
    order = crud_order.get_by_payment(db, payment_id=payment.id)
    
    if not order:
        logger.warning(f"支付记录存在但订单不存在: payment_id={payment.id}")
        return None
    
    return order


@router.post("/{order_id}/cancel", response_model=OrderCancelResponse, summary="取消订单")
async def cancel_order(
    order_id: int,
    request: OrderCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    取消订单

    根据订单状态执行不同的取消逻辑：
    - **pending（待支付）**：直接取消
    - **paid（已支付）**：发起退款
    - **completed（已完成）**：发起退款并回收消费积分
    """
    logger.info(f"取消订单: order_id={order_id}, user_id={current_user.id}, reason={request.reason}")

    from app.services.order_service import OrderCancelService
    
    result = OrderCancelService.cancel_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
        reason=request.reason
    )

    if not result.success:
        raise ForbiddenError(result.message)

    return OrderCancelResponse(
        success=result.success,
        message=result.message,
        refund_amount=str(result.refund_amount) if result.refund_amount else None,
        points_revoked=result.points_revoked
    )

