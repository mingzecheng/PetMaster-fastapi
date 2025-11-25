"""
日志管理模块

提供统一的日志配置和使用
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from app.config import settings


def setup_logger():
    """
    配置应用日志系统
    
    特点：
    - 分离不同模块的日志级别
    - 控制台和文件分别输出
    - 清晰的日志格式
    - 自动日志文件轮转
    """

    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 日志格式
    # 开发环境：简洁格式
    dev_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 生产环境：详细格式
    prod_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    formatter = dev_formatter if settings.DEBUG else prod_formatter

    # ==================== 根日志配置 ====================
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)

    # 清除已有的处理器
    root_logger.handlers.clear()

    # ==================== 控制台处理器 ====================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # ==================== 文件处理器 ====================
    # 应用日志文件
    app_log_file = log_dir / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"
    app_file_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10485760,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    app_file_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    app_file_handler.setFormatter(formatter)
    root_logger.addHandler(app_file_handler)

    # ==================== 特定模块日志配置 ====================

    # 1. SQLAlchemy 数据库日志 - 仅在DEBUG模式下显示
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_logger.setLevel(logging.WARNING)  # 默认关闭
    if settings.DEBUG:
        sqlalchemy_logger.setLevel(logging.INFO)

    # 2. SQLAlchemy 连接池日志 - 关闭
    pool_logger = logging.getLogger('sqlalchemy.pool')
    pool_logger.setLevel(logging.WARNING)

    # 3. Uvicorn 日志配置
    uvicorn_logger = logging.getLogger('uvicorn')
    uvicorn_logger.setLevel(logging.INFO)

    uvicorn_access_logger = logging.getLogger('uvicorn.access')
    uvicorn_access_logger.setLevel(logging.INFO)

    # 4. FastAPI 和 Starlette 日志
    starlette_logger = logging.getLogger('starlette')
    starlette_logger.setLevel(logging.WARNING)

    # 5. Passlib 日志（加密库）- 关闭
    passlib_logger = logging.getLogger('passlib')
    passlib_logger.setLevel(logging.WARNING)

    # 6. 应用日志
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    return root_logger


# 初始化日志
logger = setup_logger()


# ==================== 便利函数 ====================

def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称（通常使用 __name__）
    
    Returns:
        日志记录器实例
    
    Example:
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("这是一条信息日志")
    """
    return logging.getLogger(name)
