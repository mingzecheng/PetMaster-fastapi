# 导出所有Schema
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin, Token
from app.schemas.pet import PetCreate, PetUpdate, PetResponse, PetHealthRecordCreate, PetHealthRecordResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from app.schemas.boarding import BoardingCreate, BoardingUpdate, BoardingResponse
from app.schemas.transaction import TransactionCreate, TransactionResponse

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin", "Token",
    "PetCreate", "PetUpdate", "PetResponse",
    "PetHealthRecordCreate", "PetHealthRecordResponse",
    "ProductCreate", "ProductUpdate", "ProductResponse",
    "ServiceCreate", "ServiceUpdate", "ServiceResponse",
    "AppointmentCreate", "AppointmentUpdate", "AppointmentResponse",
    "BoardingCreate", "BoardingUpdate", "BoardingResponse",
    "TransactionCreate", "TransactionResponse"
]
