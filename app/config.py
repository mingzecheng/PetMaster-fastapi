from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基础配置
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    API_PREFIX: str
    HOST: str
    PORT: int

    # 数据库配置
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str

    # JWT配置
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # CORS配置
    CORS_ORIGINS: List[str]

    # 文件上传配置
    UPLOAD_DIR: str
    MAX_UPLOAD_SIZE: int
    
    # 支付配置
    PAYMENT_MODE: str = "mock"  # mock: 模拟支付（开发测试用）

    # 邮箱服务配置（QQ邮箱SMTP）
    EMAIL_ENABLED: bool = True  # 是否启用邮箱验证
    EMAIL_SMTP_HOST: str = "smtp.qq.com"  # SMTP服务器
    EMAIL_SMTP_PORT: int = 465  # SMTP端口（SSL）
    EMAIL_SENDER: str = ""  # 发送者邮箱地址（QQ邮箱）
    EMAIL_PASSWORD: str = ""  # QQ邮箱授权码（非QQ密码）
    EMAIL_CODE_EXPIRE_MINUTES: int = 5  # 验证码有效期（分钟）

    # Google reCAPTCHA 配置
    RECAPTCHA_VERSION: str  # v2 或 v3
    RECAPTCHA_V2_SECRET_KEY: str  # reCAPTCHA v2 密钥
    RECAPTCHA_V3_SECRET_KEY: str  # reCAPTCHA v3 密钥
    RECAPTCHA_ENABLED: bool   # 是否启用 reCAPTCHA
    RECAPTCHA_V3_THRESHOLD: float  # v3 专用：验证通过的最低评分

    @property
    def database_url(self) -> str:
        """构造数据库连接URL"""
        return f"mysql+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset=utf8mb4"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
