from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.crud import boarding as crud_boarding, pet as crud_pet
from app.database import get_db
from app.models.boarding import BoardingStatus
from app.models.user import User
from app.schemas.boarding import BoardingCreate, BoardingUpdate, BoardingResponse
from app.utils.dependencies import get_current_active_user, require_staff, get_current_user
from app.utils.exceptions import NotFoundError, ForbiddenError, ValidationError

router = APIRouter(prefix="/boarding", tags=["寄养管理"])


@router.post("/", response_model=BoardingResponse, status_code=status.HTTP_201_CREATED, summary="创建寄养记录")
async def create_boarding(
        boarding_in: BoardingCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """创建寄养记录"""
    # 验证宠物是否存在
    pet = crud_pet.get(db, id=boarding_in.pet_id)
    if not pet:
        raise NotFoundError("宠物不存在")

    # 普通会员只能为自己的宠物创建寄养
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise ForbiddenError("无权为此宠物创建寄养记录")

    # 验证日期
    if boarding_in.end_date <= boarding_in.start_date:
        raise ValidationError("结束日期必须大于开始日期")

    # 计算总费用
    days = (boarding_in.end_date - boarding_in.start_date).days
    if boarding_in.daily_rate:
        total_cost = float(boarding_in.daily_rate) * days
    else:
        total_cost = 0
    
    # 创建寄养记录时设置total_cost
    boarding_data = boarding_in.model_dump()
    boarding_data['total_cost'] = total_cost
    
    boarding = crud_boarding.create(db, obj_in=boarding_data)
    return boarding


@router.get("", response_model=List[BoardingResponse], summary="获取寄养列表")
async def read_boarding_list(
        skip: int = 0,
        limit: int = 100,
        pet_id: int = None,
        status_filter: BoardingStatus = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role == "member":
        # 普通会员只能查看自己宠物的寄养
        if pet_id:
            pet = crud_pet.get(db, id=pet_id)
            if not pet or pet.owner_id != current_user.id:
                raise ForbiddenError("无权查看此寄养记录")
            boarding_list = crud_boarding.get_by_pet(db, pet_id=pet_id, skip=skip, limit=limit)
            # 会员也可以按状态过滤
            if status_filter:
                boarding_list = [b for b in boarding_list if b.status == status_filter]
        else:
            # 获取当前用户所有宠物的寄养
            pets = crud_pet.get_by_owner(db, owner_id=current_user.id, skip=0, limit=1000)
            boarding_list = []
            for pet in pets:
                boarding_list.extend(crud_boarding.get_by_pet(db, pet_id=pet.id, skip=0, limit=1000))
            # 会员也可以按状态过滤
            if status_filter:
                boarding_list = [b for b in boarding_list if b.status == status_filter]
            boarding_list = boarding_list[skip:skip + limit]
        return boarding_list
    else:
        # 员工和管理员可以查看所有寄养
        if pet_id:
            boarding_list = crud_boarding.get_by_pet(db, pet_id=pet_id, skip=skip, limit=limit)
        elif status_filter:
            boarding_list = crud_boarding.get_by_status(db, status=status_filter, skip=skip, limit=limit)
        else:
            boarding_list = crud_boarding.get_multi(db, skip=skip, limit=limit)
        return boarding_list

@router.get("/ongoing", response_model=List[BoardingResponse], summary="获取进行中的寄养（员工）")
async def read_ongoing_boarding(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """获取进行中的寄养（仅员工和管理员）"""
    boarding_list = crud_boarding.get_ongoing(db, skip=skip, limit=limit)
    return boarding_list


@router.get("/{boarding_id}", response_model=BoardingResponse, summary="获取寄养详情")
async def read_boarding(
        boarding_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取寄养详情"""
    boarding = crud_boarding.get(db, id=boarding_id)
    if not boarding:
        raise NotFoundError("寄养记录不存在")

    # 普通会员只能查看自己宠物的寄养
    if current_user.role == "member":
        pet = crud_pet.get(db, id=boarding.pet_id)
        if not pet or pet.owner_id != current_user.id:
            raise ForbiddenError("无权查看此寄养记录")

    return boarding


@router.put("/{boarding_id}", response_model=BoardingResponse, summary="更新寄养信息（员工）")
async def update_boarding(
        boarding_id: int,
        boarding_in: BoardingUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """更新寄养信息（仅员工和管理员）"""
    boarding = crud_boarding.get(db, id=boarding_id)
    if not boarding:
        raise NotFoundError("寄养记录不存在")

    # 验证日期
    if boarding_in.end_date and boarding_in.start_date:
        if boarding_in.end_date <= boarding_in.start_date:
            raise ValidationError("结束日期必须大于开始日期")

    # 先更新基本字段
    boarding = crud_boarding.update(db, db_obj=boarding, obj_in=boarding_in)
    
    # 重新计算总费用
    if boarding.start_date and boarding.end_date and boarding.daily_rate:
        days = (boarding.end_date - boarding.start_date).days
        total_cost = float(boarding.daily_rate) * days
        boarding.total_cost = total_cost
        db.commit()
        db.refresh(boarding)
    
    return boarding


@router.delete("/{boarding_id}", summary="删除寄养记录（员工）")
async def delete_boarding(
        boarding_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """删除寄养记录（仅员工和管理员）"""
    boarding = crud_boarding.get(db, id=boarding_id)
    if not boarding:
        raise NotFoundError("寄养记录不存在")

    crud_boarding.delete(db, id=boarding_id)
    return {
        "message": f"寄养记录 #{boarding_id} 删除成功",
        "boarding_id": boarding_id
    }
