from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    """用户基础Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    mobile: Optional[str] = Field(None, max_length=20, description="手机号")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    role: UserRole = Field(default=UserRole.MEMBER, description="用户角色")


class UserCreate(UserBase):
    """用户创建Schema"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")


class UserUpdate(BaseModel):
    """用户更新Schema - 不包含密码字段"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    mobile: Optional[str] = Field(None, max_length=20, description="手机号")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    role: Optional[UserRole] = Field(None, description="用户角色")


# 简化的会员等级Schema（避免循环引用）
class MemberLevelSimple(BaseModel):
    """简化的会员等级Schema"""
    id: int
    name: str
    level: int
    discount_rate: float
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """用户响应Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    # 会员系统字段
    points: int = Field(default=0, description="当前可用积分")
    total_points: int = Field(default=0, description="累计获得积分")
    member_level_id: Optional[int] = Field(None, description="会员等级ID")
    member_level: Optional[MemberLevelSimple] = Field(None, description="会员等级信息")

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """用户登录Schema"""
    username: str = Field(..., description="用户名或手机号")
    password: str = Field(..., description="密码")
    recaptcha_token: Optional[str] = Field(None, description="reCAPTCHA token")


class Token(BaseModel):
    """Token响应Schema"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token数据Schema"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class ChangePassword(BaseModel):
    """密码修改Schema"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")

