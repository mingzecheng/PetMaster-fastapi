from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.crud.base import CRUDBase
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionCreate


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionCreate]):
    """交易CRUD操作类"""

    def get_by_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """根据用户ID获取交易列表"""
        return db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_type(
            self, db: Session, *, user_id: int, transaction_type: TransactionType, skip: int = 0, limit: int = 100
    ) -> List[Transaction]:
        """根据交易类型获取交易列表"""
        return db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == transaction_type
        ).offset(skip).limit(limit).all()

    def get_user_total_points(self, db: Session, *, user_id: int) -> int:
        """获取用户总积分"""
        result = db.query(func.sum(Transaction.points_change)).filter(
            Transaction.user_id == user_id
        ).scalar()
        return result if result else 0

    def get_user_total_spending(self, db: Session, *, user_id: int) -> float:
        """获取用户总消费金额"""
        result = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.type.in_([TransactionType.PURCHASE, TransactionType.SERVICE])
        ).scalar()
        return float(result) if result else 0.0


# 创建实例
transaction = CRUDTransaction(Transaction)
