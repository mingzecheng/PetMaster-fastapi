from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate, ChangePassword
from app.models.user import User
from app.crud import user as crud_user
from app.utils.dependencies import get_current_active_user, require_admin, require_staff
from app.utils.exceptions import NotFoundError, ForbiddenError
from app.utils.security import verify_password, get_password_hash

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """获取当前登录用户的信息"""
    return current_user


@router.put("/me", response_model=UserResponse, summary="更新当前用户信息")
async def update_user_me(
        user_in: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """更新当前登录用户的信息"""
    # 普通用户不能修改角色
    if user_in.role and current_user.role != "admin":
        raise ForbiddenError("无权修改用户角色")

    user = crud_user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.post("/me/change-password", summary="修改当前用户密码")
async def change_password(
        password_data: ChangePassword,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """修改当前用户密码,需要验证原密码"""
    # 验证原密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise ForbiddenError("原密码错误")
    
    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.add(current_user)
    db.commit()
    
    return {"message": "密码修改成功"}



@router.get("/", response_model=List[UserResponse], summary="获取用户列表（管理员和员工）")
async def read_users(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """获取用户列表（管理员和员工可访问）"""
    users = crud_user.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse, summary="获取指定用户信息（管理员）")
async def read_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """获取指定用户信息（仅管理员）"""
    user = crud_user.get(db, id=user_id)
    if not user:
        raise NotFoundError("用户不存在")
    return user


@router.put("/{user_id}", response_model=UserResponse, summary="更新指定用户信息（管理员）")
async def update_user(
        user_id: int,
        user_in: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """更新指定用户信息（仅管理员）"""
    user = crud_user.get(db, id=user_id)
    if not user:
        raise NotFoundError("用户不存在")

    # 防止管理员修改自己的权限
    if user_in.role and user_id == current_user.id:
        raise ForbiddenError("禁止修改自己的权限，以防失去管理员权限")

    user = crud_user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete("/{user_id}", summary="删除用户（管理员）")
async def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """删除用户（仅管理员）"""
    user = crud_user.get(db, id=user_id)
    if not user:
        raise NotFoundError("用户不存在")

    username = user.username  # 保存用户名用于响应
    crud_user.delete(db, id=user_id)
    return {
        "message": f"用户 '{username}' 删除成功",
        "user_id": user_id
    }
