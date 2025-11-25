from sqlalchemy import Column, BigInteger, String, DECIMAL, Integer, TIMESTAMP, func
from app.database import Base


class Product(Base):
    """商品库存表模型"""
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True, comment='商品ID')
    name = Column(String(100), nullable=False, index=True, comment='商品名称')
    category = Column(String(50), index=True, comment='商品分类')
    price = Column(DECIMAL(10, 2), nullable=False, comment='商品价格')
    stock = Column(Integer, default=0, comment='库存数量')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, price={self.price}, stock={self.stock})>"
