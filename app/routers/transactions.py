from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.models.user import User
from app.models.transaction import TransactionType
from app.crud import transaction as crud_transaction
from app.utils.dependencies import get_current_active_user, require_staff
from app.utils.exceptions import NotFoundError, ForbiddenError

router = APIRouter(prefix="/transactions", tags=["交易管理"])


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, summary="创建交易记录（员工）")
async def create_transaction(
        transaction_in: TransactionCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """创建交易记录（仅员工和管理员）"""
    transaction = crud_transaction.create(db, obj_in=transaction_in)
    return transaction


@router.get("/", response_model=List[TransactionResponse], summary="获取交易列表")
async def read_transactions(
        skip: int = 0,
        limit: int = 100,
        user_id: int = None,
        transaction_type: TransactionType = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    获取交易列表
    
    - **user_id**: 按用户ID筛选（员工和管理员可用）
    - **transaction_type**: 按交易类型筛选
    """
    if current_user.role == "member":
        # 普通会员只能查看自己的交易
        if transaction_type:
            transactions = crud_transaction.get_by_type(
                db, user_id=current_user.id, transaction_type=transaction_type, skip=skip, limit=limit
            )
        else:
            transactions = crud_transaction.get_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    else:
        # 员工和管理员可以查看指定用户或所有交易
        if user_id and transaction_type:
            transactions = crud_transaction.get_by_type(
                db, user_id=user_id, transaction_type=transaction_type, skip=skip, limit=limit
            )
        elif user_id:
            transactions = crud_transaction.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
        else:
            transactions = crud_transaction.get_multi(db, skip=skip, limit=limit)

    return transactions


@router.get("/me", response_model=List[TransactionResponse], summary="获取我的交易记录")
async def read_my_transactions(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的交易记录"""
    transactions = crud_transaction.get_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return transactions


@router.get("/me/points", summary="获取我的总积分")
async def read_my_points(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的总积分"""
    total_points = crud_transaction.get_user_total_points(db, user_id=current_user.id)
    return {"user_id": current_user.id, "total_points": total_points}


@router.get("/me/spending", summary="获取我的总消费")
async def read_my_spending(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的总消费金额"""
    total_spending = crud_transaction.get_user_total_spending(db, user_id=current_user.id)
    return {"user_id": current_user.id, "total_spending": total_spending}


@router.get("/{transaction_id}", response_model=TransactionResponse, summary="获取交易详情")
async def read_transaction(
        transaction_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取交易详情"""
    transaction = crud_transaction.get(db, id=transaction_id)
    if not transaction:
        raise NotFoundError("交易记录不存在")

    # 普通会员只能查看自己的交易
    if current_user.role == "member" and transaction.user_id != current_user.id:
        raise ForbiddenError("无权查看此交易记录")

    return transaction
