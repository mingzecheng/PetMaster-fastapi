from typing import List
from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.pet import PetCreate, PetUpdate, PetResponse, PetHealthRecordCreate, PetHealthRecordResponse
from app.models.user import User
from app.crud import pet as crud_pet, pet_health_record as crud_health_record
from app.utils.dependencies import get_current_active_user
from app.utils.exceptions import NotFoundError, ForbiddenError
from app.utils.file_utils import save_upload_file, delete_file

router = APIRouter(prefix="/pets", tags=["宠物管理"])


@router.post("/", response_model=PetResponse, status_code=status.HTTP_201_CREATED, summary="创建宠物档案")
async def create_pet(
        pet_in: PetCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """创建宠物档案"""
    # 普通会员只能为自己创建宠物
    if current_user.role == "member" and pet_in.owner_id != current_user.id:
        raise ForbiddenError("无权为其他用户创建宠物档案")

    pet = crud_pet.create(db, obj_in=pet_in)
    return pet


@router.get("/", response_model=List[PetResponse], summary="获取宠物列表")
async def read_pets(
        skip: int = 0,
        limit: int = 100,
        owner_id: int = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    获取宠物列表
    
    - 普通会员只能查看自己的宠物
    - 员工和管理员可以查看所有宠物或指定用户的宠物
    """
    if current_user.role == "member":
        pets = crud_pet.get_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    elif owner_id:
        pets = crud_pet.get_by_owner(db, owner_id=owner_id, skip=skip, limit=limit)
    else:
        pets = crud_pet.get_multi(db, skip=skip, limit=limit)

    return pets


@router.get("/{pet_id}", response_model=PetResponse, summary="获取宠物详情")
async def read_pet(
        pet_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取宠物详情"""
    pet = crud_pet.get(db, id=pet_id)
    if not pet:
        raise NotFoundError("宠物不存在")

    # 普通会员只能查看自己的宠物
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise ForbiddenError("无权查看此宠物信息")

    return pet


@router.put("/{pet_id}", response_model=PetResponse, summary="更新宠物信息")
async def update_pet(
        pet_id: int,
        pet_in: PetUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """更新宠物信息"""
    pet = crud_pet.get(db, id=pet_id)
    if not pet:
        raise NotFoundError("宠物不存在")

    # 普通会员只能修改自己的宠物
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise ForbiddenError("无权修改此宠物信息")

    pet = crud_pet.update(db, db_obj=pet, obj_in=pet_in)
    return pet


@router.delete("/{pet_id}", summary="删除宠物")
async def delete_pet(
        pet_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """删除宠物"""
    pet = crud_pet.get(db, id=pet_id)
    if not pet:
        raise NotFoundError("宠物不存在")

    # 普通会员只能删除自己的宠物
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise ForbiddenError("无权删除此宠物")

    # 删除宠物图片(如果有)
    if pet.image_url:
        delete_file(pet.image_url)

    pet_name = pet.name  # 保存宠物名称用于响应
    crud_pet.delete(db, id=pet_id)
    return {
        "message": f"宠物 '{pet_name}' 删除成功",
        "pet_id": pet_id
    }


# 图片上传相关接口
@router.post("/{pet_id}/upload-image", response_model=PetResponse, summary="上传宠物图片")
async def upload_pet_image(
        pet_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """上传宠物图片"""
    # 检查宠物是否存在
    pet = crud_pet.get(db, id=pet_id)
    if not pet:
        raise NotFoundError("宠物不存在")

    # 普通会员只能为自己的宠物上传图片
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise ForbiddenError("无权为此宠物上传图片")

    # 删除旧图片(如果有)
    if pet.image_url:
        delete_file(pet.image_url)

    # 保存新图片
    image_path = await save_upload_file(file, pet_id)

    # 更新宠物记录
    pet_update = PetUpdate(image_url=image_path)
    pet = crud_pet.update(db, db_obj=pet, obj_in=pet_update)

    return pet


@router.delete("/{pet_id}/image", response_model=PetResponse, summary="删除宠物图片")
async def delete_pet_image(
        pet_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """删除宠物图片"""
    # 检查宠物是否存在
    pet = crud_pet.get(db, id=pet_id)
    if not pet:
        raise NotFoundError("宠物不存在")

    # 普通会员只能删除自己宠物的图片
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise ForbiddenError("无权删除此宠物的图片")

    # 删除图片文件
    if pet.image_url:
        delete_file(pet.image_url)

    # 更新数据库记录
    pet_update = PetUpdate(image_url=None)
    pet = crud_pet.update(db, db_obj=pet, obj_in=pet_update)

    return pet


# 健康记录相关接口
@router.post("/{pet_id}/health-records", response_model=PetHealthRecordResponse, status_code=status.HTTP_201_CREATED,
             summary="添加健康记录")
async def create_health_record(
        pet_id: int,
        record_in: PetHealthRecordCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """为宠物添加健康记录"""
    # 检查宠物是否存在
    pet = crud_pet.get(db, id=pet_id)
    if not pet:
        raise NotFoundError("宠物不存在")

    # 普通会员只能为自己的宠物添加健康记录
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise ForbiddenError("无权为此宠物添加健康记录")

    # 确保记录的pet_id与URL中的一致
    record_in.pet_id = pet_id
    record = crud_health_record.create(db, obj_in=record_in)
    return record


@router.get("/{pet_id}/health-records", response_model=List[PetHealthRecordResponse], summary="获取宠物健康记录")
async def read_health_records(
        pet_id: int,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """获取宠物的健康记录列表"""
    # 检查宠物是否存在
    pet = crud_pet.get(db, id=pet_id)
    if not pet:
        raise NotFoundError("宠物不存在")

    # 普通会员只能查看自己宠物的健康记录
    if current_user.role == "member" and pet.owner_id != current_user.id:
        raise ForbiddenError("无权查看此宠物的健康记录")

    records = crud_health_record.get_by_pet(db, pet_id=pet_id, skip=skip, limit=limit)
    return records
