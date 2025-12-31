"""
邮箱服务工具类

支持QQ邮箱SMTP发送验证码邮件。
优先使用Redis存储验证码，Redis不可用时降级到内存存储。
"""

import json
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.config import settings
from app.utils.logger import get_logger
from app.utils.redis_client import RedisClient

logger = get_logger(__name__)


class EmailCodeCache:
    """
    邮箱验证码缓存管理
    
    优先使用Redis存储，Redis不可用时降级到内存存储。
    Redis Key格式: email_code:{email}:{scene}
    Redis Value格式: {"code": "123456", "created_at": "2025-12-31T16:00:00"}
    """
    
    _cache: Dict[str, Dict] = {}  # 内存缓存降级方案
    
    @classmethod
    def _get_redis_key(cls, email: str, scene: str) -> str:
        """构造Redis键名"""
        return f"email_code:{email.lower()}:{scene}"
    
    @classmethod
    def store(cls, email: str, code: str, scene: str) -> None:
        """
        存储验证码（优先使用Redis）
        
        Args:
            email: 邮箱地址
            code: 验证码
            scene: 场景（login/register/set_password/change_password）
        """
        email_lower = email.lower()
        redis_key = cls._get_redis_key(email, scene)
        
        # 准备数据
        data = {
            "code": code,
            "created_at": datetime.now().isoformat()
        }
        
        # 优先使用Redis
        if RedisClient.is_redis_enabled():
            try:
                # 使用Redis的SETEX命令，自动设置过期时间
                expire_seconds = settings.EMAIL_CODE_EXPIRE_MINUTES * 60
                RedisClient.set_value(redis_key, data, expire_seconds)
                logger.debug(f"邮箱验证码已存储到Redis: {email[:3]}***@***, 场景: {scene}, 过期时间: {settings.EMAIL_CODE_EXPIRE_MINUTES}分钟")
                return
            except Exception as e:
                logger.warning(f"Redis存储失败，降级使用内存缓存: {str(e)}")
        
        # 降级到内存缓存
        expires_at = datetime.now() + timedelta(minutes=settings.EMAIL_CODE_EXPIRE_MINUTES)
        cls._cache[redis_key] = {
            "code": code,
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        logger.debug(f"邮箱验证码已缓存到内存: {email[:3]}***@***, 场景: {scene}")
    
    @classmethod
    def verify(cls, email: str, code: str, scene: str) -> tuple[bool, str]:
        """
        验证验证码（优先从Redis读取）
        
        Args:
            email: 邮箱地址
            code: 验证码
            scene: 场景
            
        Returns:
            (是否成功, 错误信息)
        """
        email_lower = email.lower()
        redis_key = cls._get_redis_key(email, scene)
        
        # 优先从Redis读取
        if RedisClient.is_redis_enabled():
            try:
                cache_data = RedisClient.get_value(redis_key, as_json=True)
                
                if not cache_data:
                    return False, "验证码不存在或已过期"
                
                if cache_data.get("code") != code:
                    return False, "验证码错误"
                
                # 验证成功后删除
                RedisClient.delete(redis_key)
                logger.debug(f"验证码验证成功: {email[:3]}***@***, 场景: {scene}")
                return True, ""
                
            except Exception as e:
                logger.warning(f"Redis读取失败，尝试从内存缓存验证: {str(e)}")
        
        # 降级到内存缓存
        cache_data = cls._cache.get(redis_key)
        
        if not cache_data:
            return False, "验证码不存在或已过期"
        
        # 检查过期
        if datetime.now() > cache_data.get("expires_at", datetime.now()):
            cls._cache.pop(redis_key, None)
            return False, "验证码已过期"
        
        if cache_data.get("code") != code:
            return False, "验证码错误"
        
        # 验证成功后删除缓存
        cls._cache.pop(redis_key, None)
        logger.debug(f"验证码验证成功（内存缓存）: {email[:3]}***@***, 场景: {scene}")
        return True, ""
    
    @classmethod
    def can_send(cls, email: str, scene: str, interval_seconds: int = 60) -> tuple[bool, int]:
        """
        检查是否可以发送验证码（防止频繁发送）
        
        Args:
            email: 邮箱地址
            scene: 场景
            interval_seconds: 发送间隔（秒）
            
        Returns:
            (是否可以发送, 剩余等待秒数)
        """
        email_lower = email.lower()
        redis_key = cls._get_redis_key(email, scene)
        
        # 优先从Redis检查
        if RedisClient.is_redis_enabled():
            try:
                cache_data = RedisClient.get_value(redis_key, as_json=True)
                
                if not cache_data:
                    return True, 0
                
                # 解析创建时间
                created_at_str = cache_data.get("created_at")
                if created_at_str:
                    created_at = datetime.fromisoformat(created_at_str)
                    elapsed = (datetime.now() - created_at).total_seconds()
                    
                    if elapsed < interval_seconds:
                        remaining = int(interval_seconds - elapsed)
                        return False, remaining
                
                return True, 0
                
            except Exception as e:
                logger.warning(f"Redis读取失败，尝试从内存缓存检查: {str(e)}")
        
        # 降级到内存缓存
        cache_data = cls._cache.get(redis_key)
        
        if not cache_data:
            return True, 0
        
        created_at = cache_data.get("created_at", datetime.now())
        elapsed = (datetime.now() - created_at).total_seconds()
        
        if elapsed < interval_seconds:
            remaining = int(interval_seconds - elapsed)
            return False, remaining
        
        return True, 0


def generate_code(length: int = 6) -> str:
    """
    生成随机验证码
    
    Args:
        length: 验证码长度，默认6位
        
    Returns:
        数字验证码字符串
    """
    return ''.join(random.choices(string.digits, k=length))


async def send_verification_email(email: str, code: str) -> tuple[bool, str]:
    """
    发送验证码邮件
    
    Args:
        email: 收件人邮箱
        code: 验证码
        
    Returns:
        (是否成功, 错误信息或成功信息)
    """
    if not settings.EMAIL_ENABLED:
        # 未启用邮箱服务，打印到控制台
        logger.info("=" * 50)
        logger.info(f"【模拟邮件】收件人: {email}")
        logger.info(f"【模拟邮件】验证码: {code}")
        logger.info(f"【模拟邮件】有效期: {settings.EMAIL_CODE_EXPIRE_MINUTES}分钟")
        logger.info("=" * 50)
        
        print("\n" + "=" * 50)
        print(f"【模拟邮件】收件人: {email}")
        print(f"【模拟邮件】验证码: {code}")
        print(f"【模拟邮件】有效期: {settings.EMAIL_CODE_EXPIRE_MINUTES}分钟")
        print("=" * 50 + "\n")
        
        return True, "验证码已发送（模拟模式）"
    
    # 检查配置
    if not settings.EMAIL_SENDER or not settings.EMAIL_PASSWORD:
        logger.error("邮箱配置不完整")
        return False, "邮箱服务配置不完整"
    
    try:
        # 构建邮件内容
        subject = "【PetMaster】验证码"
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #FF8F00; margin: 0;">🐾 PetMaster</h1>
                <p style="color: #666; margin-top: 5px;">让养宠生活更美好</p>
            </div>
            <div style="background: #FFF8E1; border-radius: 10px; padding: 30px; text-align: center;">
                <p style="font-size: 16px; color: #333; margin-bottom: 20px;">您的验证码是：</p>
                <div style="font-size: 36px; font-weight: bold; color: #FF8F00; letter-spacing: 8px; margin: 20px 0;">
                    {code}
                </div>
                <p style="font-size: 14px; color: #666; margin-top: 20px;">
                    验证码 {settings.EMAIL_CODE_EXPIRE_MINUTES} 分钟内有效，请勿泄露给他人
                </p>
            </div>
            <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
                <p>如果这不是您的操作，请忽略此邮件</p>
            </div>
        </div>
        """
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = formataddr((str(Header('PetMaster', 'utf-8')), settings.EMAIL_SENDER))
        msg['To'] = email
        
        # 添加HTML内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 发送邮件
        logger.debug(f"正在连接SMTP服务器: {settings.EMAIL_SMTP_HOST}:{settings.EMAIL_SMTP_PORT}")
        logger.debug(f"发件人: {settings.EMAIL_SENDER}")
        
        try:
            # 创建SSL连接，设置超时
            server = smtplib.SMTP_SSL(
                settings.EMAIL_SMTP_HOST, 
                settings.EMAIL_SMTP_PORT,
                timeout=10
            )
            
            try:
                # 开启调试模式（仅在DEBUG模式下启用）
                if settings.DEBUG:
                    server.set_debuglevel(0)  # 0=关闭详细日志，1=开启详细日志
                
                logger.debug("SMTP连接成功，开始认证...")
                # 登录验证
                server.login(settings.EMAIL_SENDER, settings.EMAIL_PASSWORD)
                logger.debug("SMTP认证成功，发送邮件...")
                
                # 发送邮件
                server.sendmail(settings.EMAIL_SENDER, [email], msg.as_bytes())
                logger.info("邮件发送成功")
                
                # 邮件发送成功，立即返回，避免QUIT命令的错误
                logger.info(f"验证码邮件发送成功: {email[:3]}***@***")
                return True, "验证码已发送到您的邮箱"
                
            finally:
                # 尝试关闭连接，忽略关闭时的错误
                try:
                    server.quit()
                except Exception:
                    pass  # 忽略关闭连接时的错误
                    
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"SMTP服务器断开连接: {str(e)}")
            return False, "邮箱服务器连接失败，请检查网络"
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP认证失败: {str(e)}")
            logger.error("请检查: 1) EMAIL_SENDER是否正确 2) EMAIL_PASSWORD是否是QQ邮箱授权码（不是QQ密码）")
            return False, "邮箱认证失败，请检查邮箱地址和授权码"
        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {str(e)}")
            return False, f"邮件发送失败: {str(e)}"
        except OSError as e:
            logger.error(f"网络错误: {str(e)}")
            return False, "网络连接失败，请检查网络设置"
        except Exception as e:
            logger.error(f"未知错误: {type(e).__name__}: {str(e)}")
            return False, f"邮件发送失败: {str(e)}"
        
    except Exception as e:
        logger.error(f"邮件发送异常: {str(e)}")
        return False, f"邮件发送失败: {str(e)}"
