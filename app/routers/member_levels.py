from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.member import MemberLevel
from app.schemas.member import (
    MemberLevelCreate,
    MemberLevelUpdate,
    MemberLevelResponse
)
from app.utils.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/member_levels", tags=["会员等级"])


@router.get("/", response_model=List[MemberLevelResponse], summary="获取所有会员等级")
async def get_member_levels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取所有会员等级列表
    - 默认按等级序号升序排列
    """
    levels = db.query(MemberLevel).order_by(MemberLevel.level).offset(skip).limit(limit).all()
    return levels


@router.get("/{level_id}", response_model=MemberLevelResponse, summary="获取指定会员等级")
async def get_member_level(
    level_id: int,
    db: Session = Depends(get_db)
):
    """获取指定ID的会员等级详情"""
    level = db.query(MemberLevel).filter(MemberLevel.id == level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="会员等级不存在")
    return level


@router.post("/", response_model=MemberLevelResponse, summary="创建会员等级")
async def create_member_level(
    level_in: MemberLevelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    创建新的会员等级
    - 仅管理员可操作
    """
    # 检查等级序号是否已存在
    existing_level = db.query(MemberLevel).filter(MemberLevel.level == level_in.level).first()
    if existing_level:
        raise HTTPException(status_code=400, detail=f"等级序号 {level_in.level} 已存在")
    
    # 检查等级名称是否已存在
    existing_name = db.query(MemberLevel).filter(MemberLevel.name == level_in.name).first()
    if existing_name:
        raise HTTPException(status_code=400, detail=f"等级名称 {level_in.name} 已存在")
    
    # 创建等级
    db_level = MemberLevel(**level_in.model_dump())
    db.add(db_level)
    db.commit()
    db.refresh(db_level)
    return db_level


@router.put("/{level_id}", response_model=MemberLevelResponse, summary="更新会员等级")
async def update_member_level(
    level_id: int,
    level_update: MemberLevelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    更新会员等级信息
    - 仅管理员可操作
    """
    db_level = db.query(MemberLevel).filter(MemberLevel.id == level_id).first()
    if not db_level:
        raise HTTPException(status_code=404, detail="会员等级不存在")
    
    # 更新字段
    update_data = level_update.model_dump(exclude_unset=True)
    
    # 检查等级序号冲突
    if "level" in update_data:
        existing = db.query(MemberLevel).filter(
            MemberLevel.level == update_data["level"],
            MemberLevel.id != level_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"等级序号 {update_data['level']} 已被使用")
    
    # 检查名称冲突
    if "name" in update_data:
        existing = db.query(MemberLevel).filter(
            MemberLevel.name == update_data["name"],
            MemberLevel.id != level_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"等级名称 {update_data['name']} 已被使用")
    
    for field, value in update_data.items():
        setattr(db_level, field, value)
    
    db.commit()
    db.refresh(db_level)
    return db_level


@router.delete("/{level_id}", summary="删除会员等级")
async def delete_member_level(
    level_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    删除会员等级
    - 仅管理员可操作
    - 如果有用户关联此等级，将无法删除
    """
    db_level = db.query(MemberLevel).filter(MemberLevel.id == level_id).first()
    if not db_level:
        raise HTTPException(status_code=404, detail="会员等级不存在")
    
    # 检查是否有用户关联此等级
    from app.models.user import User
    users_count = db.query(User).filter(User.member_level_id == level_id).count()
    if users_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除，还有 {users_count} 个用户关联此等级"
        )
    
    db.delete(db_level)
    db.commit()
    return {"message": "会员等级已删除"}
