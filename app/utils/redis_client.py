"""
Redis客户端工具类

提供Redis连接管理和常用操作封装，支持降级到内存缓存。
"""

import json
from typing import Optional, Dict, Any
from datetime import timedelta
import redis
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RedisClient:
    """
    Redis客户端封装类
    
    功能：
    - 提供Redis连接池
    - 封装常用操作（set、get、delete、exists等）
    - 支持降级到内存缓存（当Redis未启用或连接失败时）
    """
    
    _client: Optional[redis.Redis] = None
    _memory_cache: Dict[str, Any] = {}  # 内存缓存降级方案
    _enabled: bool = False
    
    @classmethod
    def _get_client(cls) -> Optional[redis.Redis]:
        """
        获取Redis客户端实例（单例模式）
        
        Returns:
            Redis客户端实例，失败返回None
        """
        if not settings.REDIS_ENABLED:
            logger.warning("Redis未启用，将使用内存缓存")
            cls._enabled = False
            return None
        
        if cls._client is None:
            try:
                # 创建Redis连接池
                pool = redis.ConnectionPool.from_url(
                    settings.redis_url,
                    decode_responses=True,  # 自动解码为字符串
                    max_connections=10,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                
                # 创建Redis客户端
                cls._client = redis.Redis(connection_pool=pool)
                
                # 测试连接
                cls._client.ping()
                cls._enabled = True
                logger.info(f"Redis连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
                
            except redis.ConnectionError as e:
                logger.error(f"Redis连接失败: {str(e)}")
                logger.warning("降级使用内存缓存")
                cls._enabled = False
                cls._client = None
            except Exception as e:
                logger.error(f"Redis初始化异常: {str(e)}")
                logger.warning("降级使用内存缓存")
                cls._enabled = False
                cls._client = None
        
        return cls._client
    
    @classmethod
    def set_value(cls, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """
        设置键值对
        
        Args:
            key: 键
            value: 值（支持字符串、字典等，会自动转换为JSON）
            expire_seconds: 过期时间（秒），None表示不过期
            
        Returns:
            是否成功
        """
        client = cls._get_client()
        
        # 转换值为字符串
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = str(value)
        
        if client and cls._enabled:
            try:
                if expire_seconds:
                    client.setex(key, expire_seconds, value_str)
                else:
                    client.set(key, value_str)
                return True
            except Exception as e:
                logger.error(f"Redis SET操作失败: {str(e)}, 降级使用内存缓存")
        
        # 降级到内存缓存
        cls._memory_cache[key] = {
            "value": value_str,
            "expire_at": None if not expire_seconds else (
                __import__('datetime').datetime.now() + 
                __import__('datetime').timedelta(seconds=expire_seconds)
            )
        }
        return True
    
    @classmethod
    def get_value(cls, key: str, as_json: bool = False) -> Optional[Any]:
        """
        获取值
        
        Args:
            key: 键
            as_json: 是否将结果解析为JSON
            
        Returns:
            值，不存在或过期返回None
        """
        client = cls._get_client()
        
        if client and cls._enabled:
            try:
                value = client.get(key)
                if value is None:
                    return None
                
                if as_json:
                    return json.loads(value)
                return value
            except Exception as e:
                logger.error(f"Redis GET操作失败: {str(e)}, 尝试从内存缓存读取")
        
        # 从内存缓存读取
        cache_data = cls._memory_cache.get(key)
        if not cache_data:
            return None
        
        # 检查过期
        if cache_data["expire_at"] and __import__('datetime').datetime.now() > cache_data["expire_at"]:
            cls._memory_cache.pop(key, None)
            return None
        
        value = cache_data["value"]
        if as_json:
            return json.loads(value)
        return value
    
    @classmethod
    def delete(cls, key: str) -> bool:
        """
        删除键
        
        Args:
            key: 键
            
        Returns:
            是否成功
        """
        client = cls._get_client()
        
        if client and cls._enabled:
            try:
                client.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis DELETE操作失败: {str(e)}")
        
        # 从内存缓存删除
        cls._memory_cache.pop(key, None)
        return True
    
    @classmethod
    def exists(cls, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 键
            
        Returns:
            是否存在
        """
        client = cls._get_client()
        
        if client and cls._enabled:
            try:
                return bool(client.exists(key))
            except Exception as e:
                logger.error(f"Redis EXISTS操作失败: {str(e)}")
        
        # 检查内存缓存
        if key not in cls._memory_cache:
            return False
        
        # 检查是否过期
        cache_data = cls._memory_cache[key]
        if cache_data["expire_at"] and __import__('datetime').datetime.now() > cache_data["expire_at"]:
            cls._memory_cache.pop(key, None)
            return False
        
        return True
    
    @classmethod
    def get_ttl(cls, key: str) -> Optional[int]:
        """
        获取键的剩余过期时间
        
        Args:
            key: 键
            
        Returns:
            剩余秒数，-1表示永不过期，None表示键不存在
        """
        client = cls._get_client()
        
        if client and cls._enabled:
            try:
                ttl = client.ttl(key)
                if ttl == -2:  # 键不存在
                    return None
                return ttl
            except Exception as e:
                logger.error(f"Redis TTL操作失败: {str(e)}")
        
        # 从内存缓存计算
        cache_data = cls._memory_cache.get(key)
        if not cache_data:
            return None
        
        if cache_data["expire_at"] is None:
            return -1
        
        remaining = (cache_data["expire_at"] - __import__('datetime').datetime.now()).total_seconds()
        if remaining <= 0:
            cls._memory_cache.pop(key, None)
            return None
        
        return int(remaining)
    
    @classmethod
    def is_redis_enabled(cls) -> bool:
        """
        检查Redis是否启用且连接正常
        
        Returns:
            是否启用Redis
        """
        cls._get_client()  # 触发连接检查
        return cls._enabled


# 便捷函数封装
def set_cache(key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
    """设置缓存"""
    return RedisClient.set_value(key, value, expire_seconds)


def get_cache(key: str, as_json: bool = False) -> Optional[Any]:
    """获取缓存"""
    return RedisClient.get_value(key, as_json)


def delete_cache(key: str) -> bool:
    """删除缓存"""
    return RedisClient.delete(key)


def exists_cache(key: str) -> bool:
    """检查缓存是否存在"""
    return RedisClient.exists(key)


def get_cache_ttl(key: str) -> Optional[int]:
    """获取缓存剩余时间"""
    return RedisClient.get_ttl(key)
