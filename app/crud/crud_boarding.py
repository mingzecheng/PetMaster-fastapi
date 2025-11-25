from typing import List
from datetime import date
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.boarding import Boarding, BoardingStatus
from app.schemas.boarding import BoardingCreate, BoardingUpdate


class CRUDBoarding(CRUDBase[Boarding, BoardingCreate, BoardingUpdate]):
    """寄养CRUD操作类"""

    def get_by_pet(self, db: Session, *, pet_id: int, skip: int = 0, limit: int = 100) -> List[Boarding]:
        """根据宠物ID获取寄养列表"""
        return db.query(Boarding).filter(Boarding.pet_id == pet_id).offset(skip).limit(limit).all()

    def get_by_status(self, db: Session, *, status: BoardingStatus, skip: int = 0, limit: int = 100) -> List[Boarding]:
        """根据状态获取寄养列表"""
        return db.query(Boarding).filter(Boarding.status == status).offset(skip).limit(limit).all()

    def get_ongoing(self, db: Session, *, current_date: date = None, skip: int = 0, limit: int = 100) -> List[Boarding]:
        """获取进行中的寄养列表"""
        if current_date is None:
            current_date = date.today()

        return db.query(Boarding).filter(
            Boarding.status == BoardingStatus.ONGOING,
            Boarding.start_date <= current_date,
            Boarding.end_date >= current_date
        ).offset(skip).limit(limit).all()


# 创建实例
boarding = CRUDBoarding(Boarding)
