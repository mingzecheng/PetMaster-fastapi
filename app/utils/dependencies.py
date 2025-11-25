from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.utils.exceptions import ForbiddenError
from app.utils.security import decode_access_token

# HTTP Bearer认证
security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户
    
    Args:
        credentials: HTTP认证凭据
        db: 数据库会话
    
    Returns:
        当前用户对象
    
    Raises:
        ForbiddenError: 认证失败
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise ForbiddenError("无法验证凭据")

    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise ForbiddenError("无法验证凭据")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise ForbiddenError("无法验证凭据")

    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        当前活跃用户
    """
    return current_user


def require_role(*roles: UserRole):
    """
    角色权限依赖装饰器
    
    Args:
        roles: 允许的角色列表
    
    Returns:
        依赖函数
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError("权限不足")
        return current_user

    return role_checker


# 常用角色依赖
require_admin = require_role(UserRole.ADMIN)
require_staff = require_role(UserRole.ADMIN, UserRole.STAFF)
require_member = require_role(UserRole.ADMIN, UserRole.STAFF, UserRole.MEMBER)
