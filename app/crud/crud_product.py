from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    """商品CRUD操作类"""

    def get_by_category(self, db: Session, *, category: str, skip: int = 0, limit: int = 100) -> List[Product]:
        """根据分类获取商品列表"""
        return db.query(Product).filter(Product.category == category).offset(skip).limit(limit).all()

    def search_by_name(self, db: Session, *, name: str, skip: int = 0, limit: int = 100) -> List[Product]:
        """根据名称搜索商品"""
        return db.query(Product).filter(Product.name.like(f"%{name}%")).offset(skip).limit(limit).all()

    def update_stock(self, db: Session, *, product_id: int, quantity: int) -> Optional[Product]:
        """
        更新库存
        
        Args:
            db: 数据库会话
            product_id: 商品ID
            quantity: 库存变化量（正数增加，负数减少）
        
        Returns:
            更新后的商品对象
        """
        product = self.get(db, id=product_id)
        if product:
            product.stock += quantity
            if product.stock < 0:
                product.stock = 0
            db.add(product)
            db.commit()
            db.refresh(product)
        return product


# 创建实例
product = CRUDProduct(Product)
