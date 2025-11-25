from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


class CRUDAppointment(CRUDBase[Appointment, AppointmentCreate, AppointmentUpdate]):
    """预约CRUD操作类"""

    def get_by_pet(self, db: Session, *, pet_id: int, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """根据宠物ID获取预约列表"""
        return db.query(Appointment).filter(
            Appointment.pet_id == pet_id
        ).order_by(Appointment.appointment_time.desc()).offset(skip).limit(limit).all()

    def get_by_status(self, db: Session, *, status: AppointmentStatus, skip: int = 0, limit: int = 100) -> List[
        Appointment]:
        """根据状态获取预约列表"""
        return db.query(Appointment).filter(Appointment.status == status).offset(skip).limit(limit).all()

    def get_by_date_range(
            self, db: Session, *, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        """根据日期范围获取预约列表"""
        return db.query(Appointment).filter(
            Appointment.appointment_time >= start_date,
            Appointment.appointment_time <= end_date
        ).order_by(Appointment.appointment_time).offset(skip).limit(limit).all()

    def get_by_staff(self, db: Session, *, staff_id: int, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """根据员工ID获取预约列表"""
        return db.query(Appointment).filter(Appointment.staff_id == staff_id).offset(skip).limit(limit).all()


# 创建实例
appointment = CRUDAppointment(Appointment)
