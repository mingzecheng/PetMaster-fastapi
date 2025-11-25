from typing import List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.pet import Pet, PetHealthRecord
from app.schemas.pet import PetCreate, PetUpdate, PetHealthRecordCreate


class CRUDPet(CRUDBase[Pet, PetCreate, PetUpdate]):
    """宠物CRUD操作类"""

    def get_by_owner(self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100) -> List[Pet]:
        """根据主人ID获取宠物列表"""
        return db.query(Pet).filter(Pet.owner_id == owner_id).offset(skip).limit(limit).all()

    def get_by_species(self, db: Session, *, species: str, skip: int = 0, limit: int = 100) -> List[Pet]:
        """根据种类获取宠物列表"""
        return db.query(Pet).filter(Pet.species == species).offset(skip).limit(limit).all()


class CRUDPetHealthRecord(CRUDBase[PetHealthRecord, PetHealthRecordCreate, PetHealthRecordCreate]):
    """宠物健康记录CRUD操作类"""

    def get_by_pet(self, db: Session, *, pet_id: int, skip: int = 0, limit: int = 100) -> List[PetHealthRecord]:
        """根据宠物ID获取健康记录列表"""
        return db.query(PetHealthRecord).filter(
            PetHealthRecord.pet_id == pet_id
        ).order_by(PetHealthRecord.record_date.desc()).offset(skip).limit(limit).all()


# 创建实例
pet = CRUDPet(Pet)
pet_health_record = CRUDPetHealthRecord(PetHealthRecord)
