from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import get_password_hash, verify_password
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """用户CRUD操作类"""

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    def get_by_mobile(self, db: Session, *, mobile: str) -> Optional[User]:
        """根据手机号获取用户"""
        return db.query(User).filter(User.mobile == mobile).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """创建用户（加密密码）"""
        db_obj = User(
            username=obj_in.username,
            password_hash=get_password_hash(obj_in.password),
            mobile=obj_in.mobile,
            email=obj_in.email,
            role=obj_in.role
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        logger.info(f"用户创建成功: {obj_in.username}")
        return db_obj

    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        """更新用户（处理密码加密）"""
        update_data = obj_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["password_hash"] = hashed_password

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        logger.info(f"用户更新成功: {db_obj.id}")
        return db_obj

    def authenticate(self, db: Session, *, username: str, password: str) -> Optional[User]:
        """
        认证用户
        
        Args:
            db: 数据库会话
            username: 用户名或手机号
            password: 密码
        
        Returns:
            认证成功返回用户对象，失败返回None
        """
        user = self.get_by_username(db, username=username)
        if not user:
            user = self.get_by_mobile(db, mobile=username)

        if not user:
            logger.warning(f"用户认证失败: 不存在的用户名 {username}")
            return None
        if not verify_password(password, user.password_hash):
            logger.warning(f"用户认证失败: 用户名 {username} 的密码错误")
            return None

        logger.debug(f"用户认证成功: {username}")
        return user


# 创建用户CRUD实例
user = CRUDUser(User)
