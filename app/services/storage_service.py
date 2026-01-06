"""
统一存储服务
"""
from typing import Optional
from fastapi import UploadFile
from app.config import settings
from app.utils.logger import get_logger
from app.utils.file_utils import save_upload_file, delete_file, get_file_url

logger = get_logger(__name__)

class StorageService:
    def __init__(self):
        self.use_oss = settings.USE_OSS
        if self.use_oss:
            try:
                from app.utils.oss_utils import oss_client
                self.oss_client = oss_client
                logger.info("存储服务: 使用阿里云OSS")
            except Exception as e:
                logger.error(f"初始化OSS客户端失败，切换到本地存储: {str(e)}")
                self.use_oss = False
        else:
            logger.info("存储服务: 使用本地文件存储")
    
    async def upload(self, file: UploadFile, pet_id: int, subfolder: str = "pets") -> str:
        if self.use_oss and self.oss_client:
            return await self.oss_client.upload_to_oss(file, pet_id, subfolder)
        else:
            return await save_upload_file(file, pet_id, subfolder)
    
    def delete(self, file_path: str) -> bool:
        if file_path and file_path.startswith("http"):
            if self.use_oss and self.oss_client:
                return self.oss_client.delete_from_oss(file_path)
            else:
                logger.warning(f"OSS未启用，无法删除云文件: {file_path}")
                return False
        else:
            return delete_file(file_path)
    
    def get_url(self, file_path: Optional[str]) -> Optional[str]:
        if not file_path:
            return None
        if file_path.startswith("http"):
            return file_path
        return get_file_url(file_path)

storage_service = StorageService()
