from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    """用户基础Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    role: UserRole = Field(default=UserRole.MEMBER, description="用户角色")


class UserCreate(UserBase):
    """用户创建Schema"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")


class UserUpdate(BaseModel):
    """用户更新Schema - 不包含密码字段"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
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
    username: str = Field(..., description="用户名")
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


class EmailCodeRequest(BaseModel):
    """发送邮箱验证码请求"""
    email: EmailStr = Field(..., description="邮箱地址")
    scene: str = Field("login", pattern=r"^(login|register)$", description="场景：login/register")


class EmailCodeResponse(BaseModel):
    """发送验证码响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")


class EmailLoginRequest(BaseModel):
    """邮箱+验证码登录"""
    email: EmailStr = Field(..., description="邮箱地址")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")


class EmailRegisterRequest(BaseModel):
    """邮箱+验证码注册"""
    email: EmailStr = Field(..., description="邮箱地址")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")


class SetPasswordRequest(BaseModel):
    """首次设置密码请求（需要邮箱验证）"""
    email: EmailStr = Field(..., description="邮箱地址")
    code: str = Field(..., min_length=6, max_length=6, description="邮箱验证码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class ChangePasswordWithEmailRequest(BaseModel):
    """修改密码请求（需要邮箱验证）"""
    old_password: str = Field(..., description="原密码")
    email: EmailStr = Field(..., description="邮箱地址")
    code: str = Field(..., min_length=6, max_length=6, description="邮箱验证码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
