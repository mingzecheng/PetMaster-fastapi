"""
阿里云OSS工具类
"""
import os
import oss2
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

class OSSClient:
    def __init__(self):
        if not settings.USE_OSS:
            return
        try:
            auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
            self.bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)
            logger.info(f"OSS客户端初始化成功: {settings.OSS_BUCKET_NAME}")
        except Exception as e:
            logger.error(f"OSS客户端初始化失败: {str(e)}")
            raise
    
    def validate_image(self, file: UploadFile) -> None:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的文件类型: {file.content_type}")
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的文件扩展名: {file_ext}")
    
    def generate_unique_filename(self, pet_id: int, original_filename: str, subfolder: str = "pets") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(original_filename)[1].lower()
        filename = f"pet_{pet_id}_{timestamp}{file_ext}"
        return f"uploads/{subfolder}/{filename}"
    
    async def upload_to_oss(self, file: UploadFile, pet_id: int, subfolder: str = "pets") -> str:
        if not settings.USE_OSS:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OSS未启用")
        try:
            self.validate_image(file)
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
            if file_size > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"文件太大")
            object_key = self.generate_unique_filename(pet_id, file.filename, subfolder)
            file_content = await file.read()
            result = self.bucket.put_object(object_key, file_content)
            if result.status != 200:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"OSS上传失败")
            file_url = self.get_file_url(object_key)
            logger.info(f"文件上传成功: {object_key}")
            return file_url
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"上传文件到OSS失败: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"上传失败: {str(e)}")
        finally:
            file.file.close()
    
    def delete_from_oss(self, file_url: str) -> bool:
        if not settings.USE_OSS:
            return False
        try:
            if file_url.startswith("http"):
                parts = file_url.split("/")
                if "uploads" in parts:
                    idx = parts.index("uploads")
                    object_key = "/".join(parts[idx:])
                else:
                    return False
            else:
                object_key = file_url
            self.bucket.delete_object(object_key)
            logger.info(f"文件删除成功: {object_key}")
            return True
        except Exception as e:
            logger.error(f"从OSS删除文件失败: {str(e)}")
            return False
    
    def get_file_url(self, object_key: str) -> str:
        if settings.OSS_CUSTOM_DOMAIN:
            return f"https://{settings.OSS_CUSTOM_DOMAIN}/{object_key}"
        bucket_domain = f"{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}"
        return f"https://{bucket_domain}/{object_key}"

try:
    oss_client = OSSClient() if settings.USE_OSS else None
except Exception as e:
    logger.error(f"创建OSS客户端失败: {str(e)}")
    oss_client = None
