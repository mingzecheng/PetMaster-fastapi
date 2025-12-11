from sqlalchemy.orm import Session
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.crud.base import CRUDBase
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CRUDPayment(CRUDBase[Payment, PaymentCreate, PaymentUpdate]):
    """支付记录CRUD操作"""

    def get_by_out_trade_no(self, db: Session, out_trade_no: str) -> Payment:
        """按商户订单号查询"""
        return db.query(Payment).filter(Payment.out_trade_no == out_trade_no).first()

    def get_by_trade_no(self, db: Session, trade_no: str) -> Payment:
        """按第三方交易号查询"""
        return db.query(Payment).filter(Payment.trade_no == trade_no).first()

    def get_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list:
        """获取用户的支付记录（按时间倒序）"""
        return db.query(Payment).filter(Payment.user_id == user_id).order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_status(self, db: Session, status: PaymentStatus, skip: int = 0, limit: int = 100) -> list:
        """按支付状态查询（按时间倒序）"""
        return db.query(Payment).filter(Payment.status == status).order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()

    def get_pending_payments(self, db: Session, user_id: int = None) -> list:
        """获取待支付的记录"""
        query = db.query(Payment).filter(Payment.status == PaymentStatus.PENDING)
        if user_id:
            query = query.filter(Payment.user_id == user_id)
        return query.all()

    def get_by_related(self, db: Session, related_id: int, related_type: str) -> Payment:
        """按关联ID和类型查询"""
        return db.query(Payment).filter(
            Payment.related_id == related_id,
            Payment.related_type == related_type
        ).first()

    def update_status(self, db: Session, payment_id: int, status: PaymentStatus, **kwargs) -> Payment:
        """更新支付状态"""
        payment = self.get(db, id=payment_id)
        if payment:
            update_data = PaymentUpdate(status=status, **kwargs)
            return self.update(db, db_obj=payment, obj_in=update_data)
        return None


# 创建全局实例
payment = CRUDPayment(Payment)
