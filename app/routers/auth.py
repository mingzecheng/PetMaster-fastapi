from datetime import timedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserLogin, Token, UserCreate, UserResponse
from app.crud import user as crud_user
from app.utils.security import create_access_token
from app.config import settings
from app.utils.exceptions import ValidationError, ForbiddenError

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="用户注册")
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册接口
    
    - **username**: 用户名（唯一）
    - **password**: 密码
    - **mobile**: 手机号（可选）
    - **email**: 邮箱（可选）
    """
    # 检查用户名是否已存在
    db_user = crud_user.get_by_username(db, username=user_in.username)
    if db_user:
        raise ValidationError("用户名已存在")

    # 检查手机号是否已存在
    if user_in.mobile:
        db_user = crud_user.get_by_mobile(db, mobile=user_in.mobile)
        if db_user:
            raise ValidationError("手机号已被注册")

    # 检查邮箱是否已存在
    if user_in.email:
        db_user = crud_user.get_by_email(db, email=user_in.email)
        if db_user:
            raise ValidationError("邮箱已被注册")

    # 创建用户
    user = crud_user.create(db, obj_in=user_in)
    return user


@router.post("/login", response_model=Token, summary="用户登录")
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录接口
    
    - **username**: 用户名或手机号
    - **password**: 密码
    - **recaptcha_token**: Google reCAPTCHA v3 token (可选)
    
    返回JWT访问令牌
    """
    # 导入 reCAPTCHA 验证工具
    from app.utils.recaptcha import verify_recaptcha
    
    # 验证 reCAPTCHA (如果启用)
    if settings.RECAPTCHA_ENABLED:
        await verify_recaptcha(
            token=user_credentials.recaptcha_token or "",
            action="login"
        )
    
    # 验证用户
    user = crud_user.authenticate(
        db, username=user_credentials.username, password=user_credentials.password
    )
    if not user:
        raise ForbiddenError("用户名或密码错误")

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
