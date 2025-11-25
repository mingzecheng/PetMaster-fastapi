"""
支付宝沙箱支付集成

使用 python-alipay-sdk 3.0.4 实现支付宝沙箱支付功能
"""
from typing import Optional, Dict, Any
from alipay import AliPay

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AlipayClient:
    """支付宝客户端（基于 python-alipay-sdk 3.0.4）"""

    def __init__(self):
        """初始化支付宝客户端"""
        self.app_id = settings.ALIPAY_APP_ID
        self.app_private_key = settings.ALIPAY_APP_PRIVATE_KEY
        self.alipay_public_key = settings.ALIPAY_ALI_PUBLIC_KEY
        self.use_sandbox = settings.ALIPAY_USE_SANDBOX
        self.client = None
        self.client_initialized = False

        # 尝试创建支付宝客户端
        self._initialize_client()

    def _format_key(self, key_str: str, key_type: str = "private") -> str:
        """
        将PKCS1格式的RSA密钥转换为PEM格式
        
        Args:
            key_str: 密钥字符串
            key_type: 密钥类型，'private' 或 'public'
        
        Returns:
            PEM格式的密钥字符串
        """
        if not key_str:
            return key_str

        key_str = key_str.strip()

        # 如果已经是PEM格式，直接返回
        if key_str.startswith("-----BEGIN"):
            return key_str

        # 如果是PKCS1或PKCS8格式（没有BEGIN/END），转换为PEM格式
        if key_type == "private":
            header = "-----BEGIN RSA PRIVATE KEY-----"
            footer = "-----END RSA PRIVATE KEY-----"
        else:
            header = "-----BEGIN PUBLIC KEY-----"
            footer = "-----END PUBLIC KEY-----"

        # 将密钥分成64字符一行
        key_lines = []
        for i in range(0, len(key_str), 64):
            key_lines.append(key_str[i:i + 64])

        formatted_key = f"{header}\n" + "\n".join(key_lines) + f"\n{footer}"
        return formatted_key

    def _initialize_client(self):
        """初始化支付宝SDK客户端"""
        try:
            # 将密钥转换为PEM格式
            app_private_key = self._format_key(self.app_private_key, "private")
            alipay_public_key = self._format_key(self.alipay_public_key, "public")

            self.client = self._create_client_with_keys(app_private_key, alipay_public_key)
            self.client_initialized = True
        except ValueError as e:
            if "RSA key format" in str(e):
                logger.warning(f"支付宝RSA密钥格式错误: {str(e)}")
                logger.warning("请在 .env 文件中设置有效的 ALIPAY_APP_PRIVATE_KEY 和 ALIPAY_ALI_PUBLIC_KEY")
                logger.warning("密钥可以是PKCS1格式（无BEGIN/END行）或PEM格式（包含BEGIN/END行）")
                self.client_initialized = False
            else:
                raise

    def _create_client_with_keys(self, app_private_key: str, alipay_public_key: str) -> AliPay:
        """创建支付宝SDK客户端
        
        Args:
            app_private_key: PEM格式的应用私钥
            alipay_public_key: PEM格式的支付宝公钥
        
        Returns:
            AliPay客户端实例
        """
        # 配置网关地址
        if self.use_sandbox:
            server_url = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
        else:
            server_url = "https://openapi.alipay.com/gateway.do"

        # 创建 AliPay 实例
        alipay = AliPay(
            appid=self.app_id,
            app_notify_url=None,
            app_private_key_string=app_private_key,
            alipay_public_key_string=alipay_public_key,
            sign_type="RSA2",
            debug=self.use_sandbox
        )

        logger.info(f"支付宝客户端已创建, 沙箱模式: {self.use_sandbox}, 网关: {server_url}")
        return alipay

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
        创建支付宝请求（生成支付URL）
        Args:
            out_trade_no: 商户订单号
            total_amount: 金额（单位：元）
            subject: 商品标题
            description: 商品描述
            return_url: 支付成功后的返回URL
            notify_url: 异步通知URL
        Returns:
            支付请求结果
        """
        try:
            if not self.client_initialized or self.client is None:
                logger.error("支付宝客户端未初始化，请检查支付宝密钥配置")
                return None

            # 生成支付请求字符串
            order_string = self.client.api_alipay_trade_page_pay(
                out_trade_no=out_trade_no,
                total_amount=total_amount,
                subject=subject,
                body=description,
                return_url=return_url,
                notify_url=notify_url
            )

            # 构建完整的支付URL
            if self.use_sandbox:
                gateway_url = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
            else:
                gateway_url = "https://openapi.alipay.com/gateway.do"

            pay_url = f"{gateway_url}?{order_string}"

            logger.info(f"支付请求创建成功: {out_trade_no}")
            return {
                "pay_url": pay_url,
                "order_string": order_string,
                "code": "10000",
                "msg": "success"
            }
        except Exception as e:
            logger.error(f"创建支付请求异常: {str(e)}")
            return None

    def query_payment(self, out_trade_no: str) -> Optional[Dict[str, Any]]:
        """
        查询支付结果
        
        Args:
            out_trade_no: 商户订单号
        
        Returns:
            支付查询结果
        """
        try:
            if not self.client_initialized or self.client is None:
                logger.error("支付宝客户端未初始化，请检查支付宝密钥配置")
                return None

            # 调用查询接口
            response = self.client.api_alipay_trade_query(
                out_trade_no=out_trade_no
            )

            if response and response.get("code") == "10000":
                logger.info(f"支付查询成功: {out_trade_no}")
                return {
                    "trade_no": response.get("trade_no", ""),
                    "out_trade_no": response.get("out_trade_no", out_trade_no),
                    "trade_status": response.get("trade_status", ""),
                    "total_amount": response.get("total_amount", ""),
                    "code": response.get("code"),
                    "msg": response.get("msg", "success")
                }
            else:
                logger.error(f"支付查询失败: {response}")
                return None
        except Exception as e:
            logger.error(f"支付查询异常: {str(e)}")
            return None

    def verify_notify(self, data: Dict[str, Any]) -> bool:
        """
        验证异步通知
        
        Args:
            data: 通知数据（dict格式）
        
        Returns:
            验证结果
        """
        try:
            # 检查必要字段
            required_fields = ["trade_no", "out_trade_no", "trade_status", "total_amount"]

            for field in required_fields:
                if field not in data:
                    logger.warning(f"异步通知缺少字段: {field}")
                    return False

            # 验证签名
            sign = data.get("sign", "")
            if not sign:
                logger.warning(f"异步通知缺少签名: {data.get('out_trade_no')}")
                return False

            if not self.client_initialized or self.client is None:
                logger.warning("支付宝客户端未初始化，无法验证签名")
                # 在测试环境中，允许不验证签名直接通过
                if settings.ALIPAY_USE_SANDBOX:
                    logger.info(f"沙箱环境，跳过签名验证: {data.get('out_trade_no')}")
                    return True
                return False

            # 使用SDK验证签名
            verify_result = self.client.verify(data, sign)

            if verify_result:
                logger.info(f"异步通知验证成功: {data.get('out_trade_no')}")
                return True
            else:
                logger.warning(f"异步通知签名验证失败: {data.get('out_trade_no')}")
                return False
        except Exception as e:
            logger.error(f"异步通知验证异常: {str(e)}")
            return False


# 全局支付宝客户端实例
_alipay_client: Optional[AlipayClient] = None


def get_alipay_client() -> AlipayClient:
    """获取支付宝客户端实例"""
    global _alipay_client

    if _alipay_client is None:
        # 检查配置
        if not settings.ALIPAY_APP_ID:
            logger.warning(
                "支付宝配置不完整，请在 .env 中设置 ALIPAY_APP_ID、ALIPAY_APP_PRIVATE_KEY、ALIPAY_ALI_PUBLIC_KEY")

        _alipay_client = AlipayClient()

    return _alipay_client


def reset_alipay_client():
    """重置支付宝客户端（用于测试）"""
    global _alipay_client
    _alipay_client = None
