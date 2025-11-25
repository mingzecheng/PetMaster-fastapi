"""
Google reCAPTCHA 验证工具
支持 v2 和 v3 版本
"""
import httpx

from app.config import settings
from app.utils.exceptions import ForbiddenError
from app.utils.logger import logger


async def verify_recaptcha(token: str, action: str = "login") -> bool:
    """
    验证 reCAPTCHA token (支持 v2 和 v3)
    
    Args:
        token: 前端获取的 reCAPTCHA token
        action: 操作类型(v3 使用)，用于验证一致性(如 'login', 'register')
    
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

    # 根据版本选择密钥
    version = settings.RECAPTCHA_VERSION
    secret_key = (
        settings.RECAPTCHA_V2_SECRET_KEY
        if version == "v2"
        else settings.RECAPTCHA_V3_SECRET_KEY
    )

    if not secret_key:
        logger.error(f"reCAPTCHA {version} secret key is not configured")
        raise ForbiddenError("验证码配置错误")
    
    try:
        # 调用 Google reCAPTCHA API 验证
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": secret_key,
                    "response": token,
                },
                timeout=10.0,
            )
            
            result = response.json()
            # logger.info(f"reCAPTCHA verification result: {result}")

            # 检查验证是否成功
            if not result.get("success"):
                error_codes = result.get("error-codes", [])
                logger.warning(f"reCAPTCHA {version} verification failed: {error_codes}")
                raise ForbiddenError("验证码验证失败")

            # v3 特有：检查评分和action
            if version == "v3":
                # 检查评分
                score = result.get("score", 0)
                logger.info(f"reCAPTCHA v3 score: {score} for action: {action}")

                if score < settings.RECAPTCHA_V3_THRESHOLD:
                    logger.warning(f"reCAPTCHA v3 score too low: {score} < {settings.RECAPTCHA_V3_THRESHOLD}")
                    raise ForbiddenError(f"安全验证未通过，评分过低: {score:.2f}")

                # 检查 action 一致性(可选但推荐)
                result_action = result.get("action", "")
                if result_action != action:
                    logger.warning(f"reCAPTCHA v3 action mismatch: expected '{action}', got '{result_action}'")
                    # 注意：某些情况下 action 可能为空，不强制失败

            logger.info(f"reCAPTCHA {version} verification passed")
            return True
            
    except httpx.HTTPError as e:
        logger.error(f"reCAPTCHA API request failed: {e}")
        # 网络问题时，根据配置决定是否放行
        raise ForbiddenError("验证码服务暂时不可用，请稍后重试")
    except ForbiddenError:
        raise
    except Exception as e:
        logger.error(f"reCAPTCHA verification error: {e}")
        raise ForbiddenError("验证码验证异常")
