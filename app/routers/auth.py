from datetime import timedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import (
    UserLogin, Token, UserCreate, UserResponse,
    EmailCodeRequest, EmailCodeResponse, EmailLoginRequest, EmailRegisterRequest,
    SetPasswordRequest, ChangePasswordWithEmailRequest
)
from app.crud import user as crud_user
from app.utils.security import create_access_token, verify_password, get_password_hash
from app.utils.dependencies import get_current_user
from app.config import settings
from app.utils.exceptions import ValidationError, ForbiddenError

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="用户注册")
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册接口
    
    - **username**: 用户名（唯一）
    - **password**: 密码
    - **email**: 邮箱（可选）
    """
    # 检查用户名是否已存在
    db_user = crud_user.get_by_username(db, username=user_in.username)
    if db_user:
        raise ValidationError("用户名已存在")

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
    
    - **username**: 用户名
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


@router.post("/email/send", response_model=EmailCodeResponse, summary="发送邮箱验证码")
async def send_email_code(request: EmailCodeRequest, db: Session = Depends(get_db)):
    """
    发送邮箱验证码
    
    - **email**: 邮箱地址
    - **scene**: 场景（login=登录，register=注册）
    
    注意：
    - 登录场景：邮箱必须已注册
    - 注册场景：邮箱必须未注册
    - 60秒内不可重复发送
    """
    from app.utils.email import EmailCodeCache, generate_code, send_verification_email
    
    # 检查发送频率
    can_send, remaining = EmailCodeCache.can_send(request.email, request.scene)
    if not can_send:
        return EmailCodeResponse(success=False, message=f"请{remaining}秒后再试")
    
    # 根据场景检查邮箱状态
    existing_user = crud_user.get_by_email(db, email=request.email)
    
    if request.scene == "login":
        if not existing_user:
            raise ValidationError("该邮箱未注册")
    elif request.scene == "register":
        if existing_user:
            raise ValidationError("该邮箱已被注册")
    
    # 生成验证码
    code = generate_code()
    
    # 发送邮件
    success, message = await send_verification_email(request.email, code)
    
    if success:
        # 存储验证码
        EmailCodeCache.store(request.email, code, request.scene)
    
    return EmailCodeResponse(success=success, message=message)


@router.post("/email/login", response_model=Token, summary="邮箱验证码登录")
async def email_login(request: EmailLoginRequest, db: Session = Depends(get_db)):
    """
    邮箱+验证码登录
    
    - **email**: 邮箱地址
    - **code**: 6位验证码
    
    验证成功后返回JWT访问令牌
    """
    from app.utils.email import EmailCodeCache
    
    # 验证验证码
    valid, error_msg = EmailCodeCache.verify(request.email, request.code, "login")
    if not valid:
        raise ValidationError(error_msg)
    
    # 获取用户
    user = crud_user.get_by_email(db, email=request.email)
    if not user:
        raise ValidationError("用户不存在")
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/email/register", response_model=Token, summary="邮箱验证码注册")
async def email_register(request: EmailRegisterRequest, db: Session = Depends(get_db)):
    """
    邮箱+验证码注册
    
    - **email**: 邮箱地址
    - **code**: 6位验证码
    
    注册成功后自动登录，返回JWT访问令牌。
    系统将自动生成用户名。
    """
    from app.utils.email import EmailCodeCache
    import secrets
    
    # 验证验证码
    valid, error_msg = EmailCodeCache.verify(request.email, request.code, "register")
    if not valid:
        raise ValidationError(error_msg)
    
    # 检查邮箱是否已注册（二次校验）
    existing_user = crud_user.get_by_email(db, email=request.email)
    if existing_user:
        raise ValidationError("该邮箱已被注册")
    
    # 生成用户名: 使用邮箱前缀
    email_prefix = request.email.split('@')[0]
    username = f"user_{email_prefix[:8]}"
    
    # 检查用户名是否冲突，如果冲突则添加随机后缀
    if crud_user.get_by_username(db, username=username):
        username = f"{username}_{secrets.token_hex(2)}"
    
    # 生成随机密码（用户可以后续修改）
    random_password = secrets.token_urlsafe(12)
    
    # 创建用户
    user_in = UserCreate(
        username=username,
        password=random_password,
        email=request.email
    )
    user = crud_user.create(db, obj_in=user_in)
    
    # 创建访问令牌（自动登录）
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/set-password", summary="首次设置密码")
async def set_password(
    request: SetPasswordRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    首次设置密码（需要邮箱验证）
    
    - **email**: 邮箱地址（必须是当前用户的邮箱）
    - **code**: 6位邮箱验证码
    - **new_password**: 新密码
    
    适用于邮箱注册的用户首次设置密码。
    """
    from app.utils.email import EmailCodeCache
    
    # 验证邮箱是否属于当前用户
    if not current_user.email or current_user.email != request.email:
        raise ValidationError("邮箱地址不匹配")
    
    # 验证邮箱验证码（使用login场景，因为用户已登录，邮箱肯定存在）
    valid, error_msg = EmailCodeCache.verify(request.email, request.code, "login")
    if not valid:
        raise ValidationError(error_msg)
    
    # 更新密码
    user = crud_user.get(db, id=current_user.id)
    if user:
        user.password_hash = get_password_hash(request.new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        
    return {"message": "密码设置成功"}


@router.post("/change-password", summary="修改密码")
async def change_password(
    request: ChangePasswordWithEmailRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码（需要邮箱验证）
    
    - **old_password**: 原密码
    - **email**: 邮箱地址（必须是当前用户的邮箱）
    - **code**: 6位邮箱验证码
    - **new_password**: 新密码
    
    需要同时验证原密码和邮箱验证码，双重安全保障。
    """
    from app.utils.email import EmailCodeCache
    
    # 验证邮箱是否属于当前用户
    if not current_user.email or current_user.email != request.email:
        raise ValidationError("邮箱地址不匹配")
    
    # 获取用户信息
    user = crud_user.get(db, id=current_user.id)
    if not user:
        raise ValidationError("用户不存在")
    
    # 验证原密码
    if not verify_password(request.old_password, user.hashed_password):
        raise ValidationError("原密码错误")
    
    # 验证邮箱验证码（使用login场景，因为用户已登录，邮箱肯定存在）
    valid, error_msg = EmailCodeCache.verify(request.email, request.code, "login")
    if not valid:
        raise ValidationError(error_msg)
    
    # 更新密码
    user.password_hash = get_password_hash(request.new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "密码修改成功"}
