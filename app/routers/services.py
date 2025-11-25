from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.models.user import User
from app.models.appointment import Appointment
from app.crud import service as crud_service
from app.utils.dependencies import require_staff
from app.utils.exceptions import NotFoundError, ConflictError

router = APIRouter(prefix="/services", tags=["服务管理"])


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED, summary="创建服务项目（员工）")
async def create_service(
        service_in: ServiceCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """创建服务项目（仅员工和管理员）"""
    service = crud_service.create(db, obj_in=service_in)
    return service


@router.get("/", response_model=List[ServiceResponse], summary="获取服务列表")
async def read_services(
        skip: int = 0,
        limit: int = 100,
        name: str = None,
        db: Session = Depends(get_db)
):
    """
    获取服务列表
    
    - **name**: 按名称搜索
    """
    if name:
        services = crud_service.search_by_name(db, name=name, skip=skip, limit=limit)
    else:
        services = crud_service.get_multi(db, skip=skip, limit=limit)

    return services


@router.get("/{service_id}", response_model=ServiceResponse, summary="获取服务详情")
async def read_service(service_id: int, db: Session = Depends(get_db)):
    """获取服务详情"""
    service = crud_service.get(db, id=service_id)
    if not service:
        raise NotFoundError("服务不存在")
    return service


@router.put("/{service_id}", response_model=ServiceResponse, summary="更新服务信息（员工）")
async def update_service(
        service_id: int,
        service_in: ServiceUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """更新服务信息（仅员工和管理员）"""
    service = crud_service.get(db, id=service_id)
    if not service:
        raise NotFoundError("服务不存在")

    service = crud_service.update(db, db_obj=service, obj_in=service_in)
    return service


@router.delete("/{service_id}", summary="删除服务（员工）")
async def delete_service(
        service_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_staff)
):
    """删除服务（仅员工和管理员）"""
    service = crud_service.get(db, id=service_id)
    if not service:
        raise NotFoundError("服务不存在")

    # 检查是否存在相关的预约记录
    appointment_count = db.query(Appointment).filter(Appointment.service_id == service_id).count()
    if appointment_count > 0:
        raise ConflictError(f"无法删除服务：存在 {appointment_count} 个相关预约记录。请先处理这些预约记录。")

    service_name = service.name  # 保存服务名称用于响应
    crud_service.delete(db, id=service_id)
    return {
        "message": f"服务 '{service_name}' 删除成功",
        "service_id": service_id
    }
