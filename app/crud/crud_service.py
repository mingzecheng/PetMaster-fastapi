from typing import List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate


class CRUDService(CRUDBase[Service, ServiceCreate, ServiceUpdate]):
    """服务CRUD操作类"""

    def search_by_name(self, db: Session, *, name: str, skip: int = 0, limit: int = 100) -> List[Service]:
        """根据名称搜索服务"""
        return db.query(Service).filter(Service.name.like(f"%{name}%")).offset(skip).limit(limit).all()


# 创建实例
service = CRUDService(Service)
