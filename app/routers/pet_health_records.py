from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pet import PetHealthRecord, Pet
from app.models.user import User
from app.schemas.pet import HealthRecordCreate, HealthRecordUpdate, HealthRecordResponse
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/pet_health_records", tags=["宠物健康记录"])


@router.post("/", response_model=HealthRecordResponse, summary="创建健康记录")
async def create_health_record(
    record_in: HealthRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建宠物健康记录
    - 普通用户只能为自己的宠物创建记录
    - 管理员和员工可以为任何宠物创建记录
    """
    # 检查宠物是否存在
    pet = db.query(Pet).filter(Pet.id == record_in.pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="宠物不存在")
    
    # 权限检查
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权为此宠物创建健康记录")
    
    # 创建记录
    health_record = PetHealthRecord(**record_in.model_dump())
    db.add(health_record)
    db.commit()
    db.refresh(health_record)
    
    return health_record


@router.get("/pet/{pet_id}", response_model=List[HealthRecordResponse], summary="获取宠物的所有健康记录")
async def get_pet_health_records(
    pet_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定宠物的所有健康记录
    - 按记录日期降序排列
    """
    # 检查宠物是否存在
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="宠物不存在")
    
    # 权限检查
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此宠物的健康记录")
    
    # 查询健康记录
    records = db.query(PetHealthRecord).filter(
        PetHealthRecord.pet_id == pet_id
    ).order_by(desc(PetHealthRecord.record_date)).offset(skip).limit(limit).all()
    
    return records


@router.get("/{record_id}", response_model=HealthRecordResponse, summary="获取指定健康记录")
async def get_health_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定ID的健康记录详情"""
    record = db.query(PetHealthRecord).filter(PetHealthRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="健康记录不存在")
    
    # 权限检查
    pet = db.query(Pet).filter(Pet.id == record.pet_id).first()
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此健康记录")
    
    return record


@router.put("/{record_id}", response_model=HealthRecordResponse, summary="更新健康记录")
async def update_health_record(
    record_id: int,
    record_update: HealthRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新健康记录
    - 普通用户只能更新自己宠物的记录
    - 管理员和员工可以更新任何记录
    """
    db_record = db.query(PetHealthRecord).filter(PetHealthRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="健康记录不存在")
    
    # 权限检查
    pet = db.query(Pet).filter(Pet.id == db_record.pet_id).first()
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改此健康记录")
    
    # 更新字段
    update_data = record_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_record, field, value)
    
    db.commit()
    db.refresh(db_record)
    
    return db_record


@router.delete("/{record_id}", summary="删除健康记录")
async def delete_health_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除健康记录
    - 普通用户只能删除自己宠物的记录
    - 管理员和员工可以删除任何记录
    """
    db_record = db.query(PetHealthRecord).filter(PetHealthRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="健康记录不存在")
    
    # 权限检查
    pet = db.query(Pet).filter(Pet.id == db_record.pet_id).first()
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此健康记录")
    
    db.delete(db_record)
    db.commit()
    
    return {"message": "健康记录已删除"}
