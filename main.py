import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import (
    auth, users, pets, products, services, appointments, boarding, transactions, payments,
    member_levels, points, member_cards, pet_health_records
)
from app.utils.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    logger.info("正在启动应用...")

    # 数据库初始化
    if settings.DEBUG:
        init_db()
        logger.info("数据库初始化完成")

    # 应用配置检查
    logger.info(f"应用名称: {settings.APP_NAME}")
    logger.info(f"应用版本: {settings.APP_VERSION}")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info(f"API前缀: {settings.API_PREFIX}")
    logger.info(f"监听地址: {settings.HOST}:{settings.PORT}")

    # CORS配置检查
    logger.info(f"CORS源: {settings.CORS_ORIGINS}")
    # recaptchaV3 检查
    logger.info(f"reCAPTCHA: {settings.RECAPTCHA_ENABLED}")
    logger.info(f"RECAPTCHA_VERSION:{settings.RECAPTCHA_VERSION}")
    logger.info(f"{settings.APP_NAME} 启动成功")
    logger.info(f"API文档地址: http://localhost:{settings.PORT}{settings.API_PREFIX}/docs")

    yield
    # 停止事件
    logger.info(f"{settings.APP_NAME} 正在停止...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="宠物店管理系统 - 后端API",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan
)

# 注册全局异常处理器
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(404, http_exception_handler)
app.add_exception_handler(500, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "pets"), exist_ok=True)

# 挂载静态文件服务
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册路由
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(pets.router, prefix=settings.API_PREFIX)
app.include_router(products.router, prefix=settings.API_PREFIX)
app.include_router(services.router, prefix=settings.API_PREFIX)
app.include_router(appointments.router, prefix=settings.API_PREFIX)
app.include_router(boarding.router, prefix=settings.API_PREFIX)
app.include_router(transactions.router, prefix=settings.API_PREFIX)
app.include_router(payments.router, prefix=settings.API_PREFIX)

# 会员系统路由
app.include_router(member_levels.router, prefix=settings.API_PREFIX)
app.include_router(points.router, prefix=settings.API_PREFIX)
app.include_router(member_cards.router, prefix=settings.API_PREFIX)

# 宠物健康记录路由
app.include_router(pet_health_records.router, prefix=settings.API_PREFIX)

if __name__ == "__main__":
    """项目启动入口"""
    logger.info("正在启动 PetMaster 服务器...")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
