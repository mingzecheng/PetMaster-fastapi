# 导出所有模型，方便导入
from app.models.user import User
from app.models.pet import Pet, PetHealthRecord
from app.models.product import Product
from app.models.service import Service
from app.models.appointment import Appointment
from app.models.boarding import Boarding
from app.models.transaction import Transaction
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.member import MemberLevel, PointRecord, MemberCard, CardRechargeRecord, PointRecordType

__all__ = [
    "User",
    "Pet",
    "PetHealthRecord",
    "Product",
    "Service",
    "Appointment",
    "Boarding",
    "Transaction",
    "Payment",
    "PaymentStatus",
    "PaymentMethod",
    "MemberLevel",
    "PointRecord",
    "MemberCard",
    "CardRechargeRecord",
    "PointRecordType",
]
