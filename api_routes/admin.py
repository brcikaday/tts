from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.dependencies import require_admin_role
from db.session import get_db
from services import admin_service
from schemas.admin import (
    AdminUsersListResponse,
    AdminUserUpdate,
    AdminStatsResponse,
    AdminLogsResponse,
)

admin_router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_role)])


@admin_router.get("/users", response_model=AdminUsersListResponse)
def get_users(db: Session = Depends(get_db)):
    return {"users": admin_service.list_users(db)}


@admin_router.put("/users/{id}")
def put_user(id: int, update_data: AdminUserUpdate, db: Session = Depends(get_db), current_user=Depends(require_admin_role)):
    admin_service.update_user(id, update_data, db, actor_id=current_user.id)
    return {"message": "User updated"}


@admin_router.get("/stats", response_model=AdminStatsResponse)
def get_stats(db: Session = Depends(get_db)):
    return admin_service.get_stats(db)


@admin_router.get("/logs", response_model=AdminLogsResponse)
def get_logs(db: Session = Depends(get_db), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return {"logs": admin_service.get_logs(db, limit, offset), "limit": limit, "offset": offset}
