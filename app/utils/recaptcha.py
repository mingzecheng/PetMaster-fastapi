"""
Google reCAPTCHA v3 验证工具
"""
import httpx
from app.config import settings
from app.utils.exceptions import ForbiddenError
from app.utils.logger import logger


async def verify_recaptcha(token: str, action: str = "login") -> bool:
    """
    验证 reCAPTCHA v3 token
    
    Args:
        token: 前端获取的 reCAPTCHA token
        action: 操作类型，用于验证一致性(如 'login', 'register')
    
    Returns:
        验证是否通过
        
    Raises:
        ForbiddenError: 验证失败时抛出
    """
    # 如果未启用 reCAPTCHA，直接通过
    if not settings.RECAPTCHA_ENABLED:
        logger.debug("reCAPTCHA is disabled, skipping verification")
        return True
    
    # 检查 token 是否存在
    if not token:
        logger.warning("reCAPTCHA token is missing")
        raise ForbiddenError("验证码缺失")
    
    try:
        # 调用 Google reCAPTCHA API 验证
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": settings.RECAPTCHA_SECRET_KEY,
                    "response": token,
                },
                timeout=10.0,
            )
            
            result = response.json()
            
            # 检查验证是否成功
            if not result.get("success"):
                error_codes = result.get("error-codes", [])
                logger.warning(f"reCAPTCHA verification failed: {error_codes}")
                raise ForbiddenError("验证码验证失败")
            
            # 检查评分
            score = result.get("score", 0)
            logger.info(f"reCAPTCHA score: {score} for action: {action}")
            
            if score < settings.RECAPTCHA_THRESHOLD:
                logger.warning(f"reCAPTCHA score too low: {score} < {settings.RECAPTCHA_THRESHOLD}")
                raise ForbiddenError(f"安全验证未通过，评分过低: {score:.2f}")
            
            # 检查 action 一致性(可选但推荐)
            result_action = result.get("action", "")
            if result_action != action:
                logger.warning(f"reCAPTCHA action mismatch: expected '{action}', got '{result_action}'")
                # 注意：某些情况下 action 可能为空，不强制失败
                # raise ForbiddenError("验证码操作不匹配")
            
            logger.debug(f"reCAPTCHA verification passed for action: {action}")
            return True
            
    except httpx.HTTPError as e:
        logger.error(f"reCAPTCHA API request failed: {e}")
        # 网络问题时，根据配置决定是否放行
        # 生产环境建议失败时拒绝，开发环境可以考虑放行
        raise ForbiddenError("验证码服务暂时不可用，请稍后重试")
    except ForbiddenError:
        raise
    except Exception as e:
        logger.error(f"reCAPTCHA verification error: {e}")
        raise ForbiddenError("验证码验证异常")
