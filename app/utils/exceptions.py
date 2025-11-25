import traceback

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.logger import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """应用自定义异常基类"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AppException):
    """数据验证异常"""

    def __init__(self, message: str):
        super().__init__(message, 400)


class NotFoundError(AppException):
    """资源未找到异常"""

    def __init__(self, message: str):
        super().__init__(message, 404)


class ForbiddenError(AppException):
    """权限不足异常"""

    def __init__(self, message: str):
        super().__init__(message, 403)


class ConflictError(AppException):
    """资源冲突异常"""

    def __init__(self, message: str):
        super().__init__(message, 409)


async def app_exception_handler(request: Request, exc: AppException):
    """应用自定义异常处理器"""
    logger.error(f"应用异常: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message
            }
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常 {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail
            }
        }
    )


async def validation_exception_handler(request: Request, exc: Exception):
    """请求验证异常处理器"""
    logger.warning(f"请求验证异常: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "ValidationException",
                "message": "请求数据验证失败",
                "details": str(exc)
            }
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """数据库异常处理器"""
    logger.error(f"数据库异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "DatabaseError",
                "message": "数据库操作失败"
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理异常: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "服务器内部错误"
            }
        }
    )
