from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from app.models.user import User
from app.models.appointment import AppointmentStatus
from app.crud import appointment as crud_appointment, pet as crud_pet, service as crud_service
from app.utils.dependencies import get_current_active_user, require_staff
from app.utils.exceptions import NotFoundError, ForbiddenError

router = APIRouter(prefix="/appointments", tags=["预约管理"])


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED, summary="创建预约")
async def create_appointment(
        appointment_in: AppointmentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """创建预约"""
    # 验证宠物是否存在
    pet = crud_pet.get(db, id=appointment_in.pet_id)
    if not pet:
        raise NotFoundError("宠物不存在")

    # 普通会员只能为自己的宠物预约
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise ForbiddenError("无权为此宠物创建预约")

    # 验证服务是否存在
    service = crud_service.get(db, id=appointment_in.service_id)
    if not service:
        raise NotFoundError("服务不存在")

    appointment = crud_appointment.create(db, obj_in=appointment_in)
    return appointment


@router.get("/", response_model=List[AppointmentResponse], summary="获取预约列表")
async def read_appointments(
        skip: int = 0,
        limit: int = 100,
        pet_id: int = None,
        status_filter: AppointmentStatus = None,
        start_date: datetime = None,
        end_date: datetime = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    获取预约列表
    
    - **pet_id**: 按宠物ID筛选
    - **status**: 按状态筛选
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    """
    if current_user.role == "member":
        # 普通会员只能查看自己宠物的预约
        if pet_id:
            pet = crud_pet.get(db, id=pet_id)
            if not pet or pet.owner_id != current_user.id:
                raise ForbiddenError("无权查看此预约")
            appointments = crud_appointment.get_by_pet(db, pet_id=pet_id, skip=skip, limit=limit)
        else:
            # 获取当前用户所有宠物的预约
            pets = crud_pet.get_by_owner(db, owner_id=current_user.id, skip=0, limit=1000)
            appointments = []
            for pet in pets:
                appointments.extend(crud_appointment.get_by_pet(db, pet_id=pet.id, skip=0, limit=1000))
            appointments = appointments[skip:skip + limit]
    else:
        # 员工和管理员可以查看所有预约
        if pet_id:
            appointments = crud_appointment.get_by_pet(db, pet_id=pet_id, skip=skip, limit=limit)
        elif status_filter:
            appointments = crud_appointment.get_by_status(db, status=status_filter, skip=skip, limit=limit)
        elif start_date and end_date:
            appointments = crud_appointment.get_by_date_range(
                db, start_date=start_date, end_date=end_date, skip=skip, limit=limit
            )
        else:
            appointments = crud_appointment.get_multi(db, skip=skip, limit=limit)

    return appointments


@router.get("/{appointment_id}", response_model=AppointmentResponse, summary="获取预约详情")
async def read_appointment(
        appointment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取预约详情"""
    appointment = crud_appointment.get(db, id=appointment_id)
    if not appointment:
        raise NotFoundError("预约不存在")

    # 普通会员只能查看自己宠物的预约
    if current_user.role == "member":
        pet = crud_pet.get(db, id=appointment.pet_id)
        if not pet or pet.owner_id != current_user.id:
            raise ForbiddenError("无权查看此预约")

    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse, summary="更新预约信息")
async def update_appointment(
        appointment_id: int,
        appointment_in: AppointmentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """更新预约信息"""
    appointment = crud_appointment.get(db, id=appointment_id)
    if not appointment:
        raise NotFoundError("预约不存在")

    # 普通会员只能修改自己宠物的预约，且不能修改状态
    if current_user.role == "member":
        pet = crud_pet.get(db, id=appointment.pet_id)
        if not pet or pet.owner_id != current_user.id:
            raise ForbiddenError("无权修改此预约")
        if appointment_in.status:
            raise ForbiddenError("无权修改预约状态")

    appointment = crud_appointment.update(db, db_obj=appointment, obj_in=appointment_in)
    return appointment


@router.delete("/{appointment_id}", summary="取消预约")
async def cancel_appointment(
        appointment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """取消预约"""
    appointment = crud_appointment.get(db, id=appointment_id)
    if not appointment:
        raise NotFoundError("预约不存在")

    # 普通会员只能取消自己宠物的预约
    if current_user.role == "member":
        pet = crud_pet.get(db, id=appointment.pet_id)
        if not pet or pet.owner_id != current_user.id:
            raise ForbiddenError("无权取消此预约")

    # 更新状态为已取消
    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)
    return {
        "message": f"预约 #{appointment_id} 已成功取消",
        "appointment_id": appointment_id
    }
