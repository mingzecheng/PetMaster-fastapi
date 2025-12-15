# 导出所有CRUD操作实例
from app.crud.crud_user import user
from app.crud.crud_pet import pet, pet_health_record
from app.crud.crud_product import crud_product as product
from app.crud.crud_service import service
from app.crud.crud_appointment import appointment
from app.crud.crud_boarding import boarding
from app.crud.crud_transaction import transaction
from app.crud.crud_payment import payment
from app.crud.crud_order import crud_order

__all__ = [
    "user",
    "pet",
    "pet_health_record",
    "product",
    "service",
    "appointment",
    "boarding",
    "transaction",
    "payment",
    "crud_order"
]
