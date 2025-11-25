from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import product as crud_product
from app.database import get_db
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.utils.dependencies import require_staff
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/products", tags=["商品管理"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="创建商品（员工）")
async def create_product(
        product_in: ProductCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """创建商品（仅员工和管理员）"""
    product = crud_product.create(db, obj_in=product_in)
    return product


@router.get("/", response_model=List[ProductResponse], summary="获取商品列表")
async def read_products(
        skip: int = 0,
        limit: int = 100,
        category: str = None,
        name: str = None,
        db: Session = Depends(get_db)
):
    """
    获取商品列表
    
    - **category**: 按分类筛选
    - **name**: 按名称搜索
    """
    if category:
        products = crud_product.get_by_category(db, category=category, skip=skip, limit=limit)
    elif name:
        products = crud_product.search_by_name(db, name=name, skip=skip, limit=limit)
    else:
        products = crud_product.get_multi(db, skip=skip, limit=limit)

    return products


@router.get("/{product_id}", response_model=ProductResponse, summary="获取商品详情")
async def read_product(product_id: int, db: Session = Depends(get_db)):
    """获取商品详情"""
    product = crud_product.get(db, id=product_id)
    if not product:
        raise NotFoundError("商品不存在")
    return product


@router.put("/{product_id}", response_model=ProductResponse, summary="更新商品信息（员工）")
async def update_product(
        product_id: int,
        product_in: ProductUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """更新商品信息（仅员工和管理员）"""
    product = crud_product.get(db, id=product_id)
    if not product:
        raise NotFoundError("商品不存在")

    product = crud_product.update(db, db_obj=product, obj_in=product_in)
    return product


@router.delete("/{product_id}", summary="删除商品（员工）")
async def delete_product(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """删除商品（仅员工和管理员）"""
    product = crud_product.get(db, id=product_id)
    if not product:
        raise NotFoundError("商品不存在")

    product_name = product.name  # 保存商品名称用于响应
    crud_product.delete(db, id=product_id)
    return {
        "message": f"商品 '{product_name}' 删除成功",
        "product_id": product_id
    }


@router.patch("/{product_id}/stock", response_model=ProductResponse, summary="更新商品库存（员工）")
async def update_product_stock(
        product_id: int,
        quantity: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """
    更新商品库存（仅员工和管理员）
    - **quantity**: 库存变化量（正数增加，负数减少）
    """
    product = crud_product.update_stock(db, product_id=product_id, quantity=quantity)
    if not product:
        raise NotFoundError("商品不存在")

    return product
