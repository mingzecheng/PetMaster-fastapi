"""
支付宝支付工具模块
使用官方 alipay-sdk-python SDK
"""
from typing import Optional, Dict, Any

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.domain.AlipayTradeQueryModel import AlipayTradeQueryModel
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest
from alipay.aop.api.response.AlipayTradeQueryResponse import AlipayTradeQueryResponse

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AlipayClient:
    """支付宝客户端封装类（使用官方SDK）"""

    def __init__(self):
        """初始化支付宝客户端"""
        self.app_id = settings.ALIPAY_APP_ID
        self.app_private_key = settings.ALIPAY_APP_PRIVATE_KEY
        self.alipay_public_key = settings.ALIPAY_ALI_PUBLIC_KEY
        self.use_sandbox = settings.ALIPAY_USE_SANDBOX
        
        self.client: Optional[DefaultAlipayClient] = None
        self.client_initialized = False
        
        # 禁用沙箱环境的SSL证书验证
        if self.use_sandbox:
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            logger.warning("沙箱环境已禁用 SSL 证书验证，生产环境请勿使用此配置")
        
        self._initialize_client()

    def _format_private_key(self, key_str: str) -> str:
        """
        格式化应用私钥为标准PEM格式
        
        Args:
            key_str: 私钥字符串
            
        Returns:
            PEM格式的私钥字符串
        """
        if not key_str:
            return ""
        
        key_str = key_str.strip()
        
        # 如果已经是PEM格式，直接返回
        if key_str.startswith("-----BEGIN"):
            return key_str
        
        # 移除空格和换行
        key_str = key_str.replace(' ', '').replace('\n', '').replace('\r', '')
        
        # 添加PEM头尾
        # 官方SDK通常使用PKCS8格式，但也兼容PKCS1
        # 这里使用PKCS1格式（非Java推荐）
        header = "-----BEGIN RSA PRIVATE KEY-----"
        footer = "-----END RSA PRIVATE KEY-----"
        
        # 格式化为每64字符一行
        formatted_lines = []
        for i in range(0, len(key_str), 64):
            formatted_lines.append(key_str[i:i+64])
        
        return f"{header}\n" + "\n".join(formatted_lines) + f"\n{footer}"

    def _format_public_key(self, key_str: str) -> str:
        """
        格式化支付宝公钥为标准PEM格式
        
        Args:
            key_str: 公钥字符串
            
        Returns:
            PEM格式的公钥字符串
        """
        if not key_str:
            return ""
        
        key_str = key_str.strip()
        
        # 如果已经是PEM格式，直接返回
        if key_str.startswith("-----BEGIN"):
            return key_str
        
        #移除空格和换行
        key_str = key_str.replace(' ', '').replace('\n', '').replace('\r', '')
        
        # 添加PEM头尾
        header = "-----BEGIN PUBLIC KEY-----"
        footer = "-----END PUBLIC KEY-----"
        
        # 格式化为每64字符一行
        formatted_lines = []
        for i in range(0, len(key_str), 64):
            formatted_lines.append(key_str[i:i+64])
        
        return f"{header}\n" + "\n".join(formatted_lines) + f"\n{footer}"

    def _initialize_client(self):
        """初始化支付宝客户端"""
        try:
            logger.info("[官方SDK] 开始初始化支付宝客户端")
            logger.info(f"[官方SDK] APP_ID: {self.app_id}")
            logger.info(f"[官方SDK] 沙箱模式: {self.use_sandbox}")
            
            # 创建客户端配置
            alipay_client_config = AlipayClientConfig()
            alipay_client_config.app_id = self.app_id
            
            # 格式化密钥
            formatted_private_key = self._format_private_key(self.app_private_key)
            formatted_public_key = self._format_public_key(self.alipay_public_key)
            
            logger.info(f"[官方SDK] 私钥前50字符: {formatted_private_key[:50]}...")
            logger.info(f"[官方SDK] 公钥前50字符: {formatted_public_key[:50]}...")
            
            # 设置密钥
            alipay_client_config.app_private_key = formatted_private_key
            alipay_client_config.alipay_public_key = formatted_public_key
            
            # 设置网关地址
            if self.use_sandbox:
                alipay_client_config.server_url = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
            else:
                alipay_client_config.server_url = "https://openapi.alipay.com/gateway.do"
            
            logger.info(f"[官方SDK] 网关地址: {alipay_client_config.server_url}")
            
            # 设置签名类型
            alipay_client_config.sign_type = "RSA2"
            
            # 创建客户端实例
            self.client = DefaultAlipayClient(alipay_client_config=alipay_client_config)
            self.client_initialized = True
            
            logger.info("[官方SDK] 支付宝客户端初始化成功")
            
        except Exception as e:
            logger.error(f"[官方SDK] 初始化失败: {str(e)}")
            import traceback
            logger.error(f"[官方SDK] 错误堆栈: {traceback.format_exc()}")
            self.client_initialized = False

    def create_payment(
            self,
            out_trade_no: str,
            total_amount: str,
            subject: str,
            description: str = "",
            return_url: str = "",
            notify_url: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        创建支付宝页面支付请求（电脑网站支付）
        
        Args:
            out_trade_no: 商户订单号
            total_amount: 订单金额（单位：元）
            subject: 订单标题
            description: 订单描述
            return_url: 同步回调地址
            notify_url: 异步通知地址
            
        Returns:
            支付请求结果
        """
        try:
            if not self.client_initialized or self.client is None:
                logger.error("[官方SDK] 客户端未初始化，无法创建支付")
                return None
            
            logger.info(f"[官方SDK] 创建支付请求: {out_trade_no}, 金额: {total_amount}")
            logger.info(f"[官方SDK] notify_url: {notify_url}")
            logger.info(f"[官方SDK] return_url: {return_url}")
            
            # 创建请求模型
            model = AlipayTradePagePayModel()
            model.out_trade_no = out_trade_no
            model.total_amount = total_amount
            model.subject = subject
            model.body = description
            model.product_code = "FAST_INSTANT_TRADE_PAY"
            
            # 创建请求对象
            request = AlipayTradePagePayRequest(biz_model=model)
            request.return_url = return_url
            request.notify_url = notify_url
            
            # 发起请求，page_execute 返回的是完整的支付URL（字符串）
            pay_url = self.client.page_execute(request, http_method="GET")
            
            logger.info(f"[官方SDK] 支付URL生成成功")
            logger.info(f"[官方SDK] URL长度: {len(pay_url)}")
            
            return {
                "pay_url": pay_url,
                "code": "10000",
                "msg": "success"
            }
                
        except Exception as e:
            logger.error(f"[官方SDK] 创建支付异常: {str(e)}")
            import traceback
            logger.error(f"[官方SDK] 异常堆栈: {traceback.format_exc()}")
            return None

    def query_payment(self, out_trade_no: str) -> Optional[Dict[str, Any]]:
        """
        查询支付订单状态
        
        Args:
            out_trade_no: 商户订单号
            
        Returns:
            订单查询结果
        """
        try:
            if not self.client_initialized or self.client is None:
                logger.error("[官方SDK] 客户端未初始化，无法查询支付")
                return None
            
            logger.info(f"[官方SDK] 查询支付状态: {out_trade_no}")
            
            # 创建查询模型
            model = AlipayTradeQueryModel()
            model.out_trade_no = out_trade_no
            
            # 创建请求对象
            request = AlipayTradeQueryRequest(biz_model=model)
            
            # 发起查询 - execute返回的是响应对象
            response_content: AlipayTradeQueryResponse = self.client.execute(request)
            
            # 解析响应（官方SDK的execute返回的是response对象）
            logger.info(f"[官方SDK] 查询响应: {response_content}")
            
            # 检查响应
            if hasattr(response_content, 'code') and response_content.code == "10000":
                # 查询成功
                return {
                    "code": response_content.code,
                    "msg": response_content.msg,
                    "trade_no": getattr(response_content, 'trade_no', ''),
                    "out_trade_no": getattr(response_content, 'out_trade_no', ''),
                    "trade_status": getattr(response_content, 'trade_status', ''),
                    "total_amount": getattr(response_content, 'total_amount', ''),
                }
            else:
                # 查询失败或订单不存在
                logger.warning(f"[官方SDK] 查询失败或订单不存在: {response_content}")
                return None
                
        except Exception as e:
            logger.error(f"[官方SDK] 查询支付异常: {str(e)}")
            import traceback
            logger.error(f"[官方SDK] 异常堆栈: {traceback.format_exc()}")
            return None

    def verify_notify(self, params: Dict[str, Any]) -> bool:
        """
        验证支付宝异步通知签名
        
        Args:
            params: 通知参数
            
        Returns:
            验证是否通过
        """
        try:
            if not self.client_initialized or self.client is None:
                logger.error("[官方SDK] 客户端未初始化，无法验证签名")
                return False
            
            logger.info("[官方SDK] 验证异步通知签名")
            
            # 使用SDK验证签名
            result = self.client.verify(params)
            
            logger.info(f"[官方SDK] 签名验证结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"[官方SDK] 验证签名异常: {str(e)}")
            import traceback
            logger.error(f"[官方SDK] 异常堆栈: {traceback.format_exc()}")
            return False


# 创建全局单例
alipay_client = AlipayClient()
