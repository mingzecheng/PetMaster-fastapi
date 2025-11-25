import os
import shutil
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 允许的图片格式
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp"
}

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def validate_image(file: UploadFile) -> None:
    """
    验证上传的图片文件
    
    Args:
        file: 上传的文件对象
    
    Raises:
        HTTPException: 如果文件验证失败
    """
    # 检查文件类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file.content_type}。仅支持 JPEG, PNG, GIF, WebP 格式"
        )

    # 检查文件扩展名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件扩展名: {file_ext}"
        )

    logger.info(f"文件验证通过: {file.filename} ({file.content_type})")


def generate_unique_filename(pet_id: int, original_filename: str) -> str:
    """
    生成唯一的文件名
    
    Args:
        pet_id: 宠物ID
        original_filename: 原始文件名
    
    Returns:
        唯一的文件名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = os.path.splitext(original_filename)[1].lower()
    return f"pet_{pet_id}_{timestamp}{file_ext}"


async def save_upload_file(
        file: UploadFile,
        pet_id: int,
        subfolder: str = "pets"
) -> str:
    """
    保存上传的文件
    
    Args:
        file: 上传的文件对象
        pet_id: 宠物ID
        subfolder: 子文件夹名称
    
    Returns:
        保存的文件相对路径
    
    Raises:
        HTTPException: 如果保存失败
    """
    try:
        # 验证文件
        validate_image(file)

        # 创建保存目录
        upload_dir = os.path.join(settings.UPLOAD_DIR, subfolder)
        os.makedirs(upload_dir, exist_ok=True)

        # 生成唯一文件名
        filename = generate_unique_filename(pet_id, file.filename)
        file_path = os.path.join(upload_dir, filename)

        # 检查文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()  # 获取文件大小
        file.file.seek(0)  # 重置到开头

        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件太大。最大允许: {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.1f}MB"
            )

        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 返回相对路径
        relative_path = os.path.join(subfolder, filename)
        logger.info(f"文件保存成功: {relative_path}")

        return relative_path

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存文件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存文件失败: {str(e)}"
        )
    finally:
        file.file.close()


def delete_file(file_path: Optional[str]) -> bool:
    """
    删除指定文件
    
    Args:
        file_path: 文件相对路径
    
    Returns:
        是否删除成功
    """
    if not file_path:
        return False

    try:
        # 构建完整路径
        full_path = os.path.join(settings.UPLOAD_DIR, file_path)

        # 检查文件是否存在
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"文件删除成功: {file_path}")
            return True
        else:
            logger.warning(f"文件不存在: {file_path}")
            return False

    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        return False


def get_file_url(file_path: Optional[str]) -> Optional[str]:
    """
    获取文件的访问URL
    
    Args:
        file_path: 文件相对路径
    
    Returns:
        文件访问URL
    """
    if not file_path:
        return None

    # 返回相对URL路径(前端会拼接完整URL)
    return f"/uploads/{file_path}"
