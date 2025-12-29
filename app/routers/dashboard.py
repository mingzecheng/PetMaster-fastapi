"""
仪表盘统计API路由
提供后台管理系统的统计数据
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast, Date
from datetime import date, datetime
from pydantic import BaseModel
from decimal import Decimal

from app.database import get_db
from app.models.user import User, UserRole
from app.models.pet import Pet
from app.models.appointment import Appointment
from app.models.payment import Payment, PaymentStatus
from app.utils.dependencies import get_current_active_user
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["仪表盘统计"])


class DashboardStats(BaseModel):
    """仪表盘统计数据"""
    total_users: int
    total_admins: int
    total_staff: int
    total_members: int
    total_pets: int
    today_appointments: int
    today_revenue: Decimal
    
    class Config:
        from_attributes = True


@router.get("/stats/", response_model=DashboardStats, summary="获取仪表盘统计数据")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取仪表盘统计数据
    
    - **total_users**: 总用户数
    - **total_admins**: 管理员数量
    - **total_staff**: 员工数量
    - **total_members**: 会员数量
    - **total_pets**: 宠物总数
    - **today_appointments**: 今日预约数
    - **today_revenue**: 今日营收（来自 payments.amount）
    """
    logger.info(f"获取仪表盘统计数据: user_id={current_user.id}")
    
    # 1. 统计用户数（按角色分类）
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_admins = db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN).scalar() or 0
    total_staff = db.query(func.count(User.id)).filter(User.role == UserRole.STAFF).scalar() or 0
    total_members = db.query(func.count(User.id)).filter(User.role == UserRole.MEMBER).scalar() or 0
    
    # 2. 统计宠物总数
    total_pets = db.query(func.count(Pet.id)).scalar() or 0
    
    # 3. 统计今日预约数
    today = date.today()
    today_appointments = db.query(func.count(Appointment.id)).filter(
        cast(Appointment.appointment_time, Date) == today
    ).scalar() or 0
    
    # 4. 统计今日营收（从 payments 表，使用 amount 字段）
    today_revenue_result = db.query(
        func.sum(Payment.amount)
    ).filter(
        and_(
            cast(Payment.paid_at, Date) == today,
            Payment.status == PaymentStatus.PAID
        )
    ).scalar()
    
    today_revenue = today_revenue_result or Decimal('0.00')
    
    logger.info(
        f"统计数据: users={total_users}, pets={total_pets}, "
        f"today_appointments={today_appointments}, today_revenue={today_revenue}"
    )
    
    return DashboardStats(
        total_users=total_users,
        total_admins=total_admins,
        total_staff=total_staff,
        total_members=total_members,
        total_pets=total_pets,
        today_appointments=today_appointments,
        today_revenue=today_revenue
    )


class TrendData(BaseModel):
    """趋势数据"""
    date: str
    appointments: int
    revenue: Decimal
    boarding: int
    
    class Config:
        from_attributes = True


@router.get("/trends/", response_model=list[TrendData], summary="获取最近7天趋势数据")
async def get_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取最近7天的趋势数据
    - **date**: 日期
    - **appointments**: 预约数
    - **revenue**: 营收
    - **boarding**: 寄养数
    """
    from datetime import timedelta
    from app.models.boarding import Boarding
    
    today = date.today()
    result = []
    
    # 获取最近7天的数据
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        
        # 统计预约数
        appointments_count = db.query(func.count(Appointment.id)).filter(
            cast(Appointment.appointment_time, Date) == target_date
        ).scalar() or 0
        
        # 统计营收
        revenue_sum = db.query(func.sum(Payment.amount)).filter(
            and_(
                cast(Payment.paid_at, Date) == target_date,
                Payment.status == PaymentStatus.PAID
            )
        ).scalar() or Decimal('0.00')
        
        # 统计寄养数
        boarding_count = db.query(func.count(Boarding.id)).filter(
            cast(Boarding.start_date, Date) == target_date
        ).scalar() or 0
        
        result.append(TrendData(
            date=target_date.isoformat(),
            appointments=appointments_count,
            revenue=revenue_sum,
            boarding=boarding_count
        ))
    
    return result
