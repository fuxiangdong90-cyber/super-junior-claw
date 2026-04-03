"""通知与系统配置API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, update
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.extended import Notification, SystemConfig, AuditLog, APIKey, Webhook, Invitation

router = APIRouter(prefix="/notifications", tags=["通知"])


@router.get("")
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取通知列表"""
    query = select(Notification).where(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.where(Notification.is_read == False)
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)
    
    query = query.order_by(desc(Notification.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    # 获取未读数
    unread_result = await db.execute(
        select(Notification).where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            )
        )
    )
    unread_count = len(unread_result.scalars().all())
    
    return {
        "items": [NotificationResponse.model_validate(n) for n in notifications],
        "unread_count": unread_count,
        "page": page,
        "page_size": page_size
    }


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """标记通知为已读"""
    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == current_user.id
            )
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Marked as read"}


@router.post("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """标记所有通知为已读"""
    await db.execute(
        update(Notification)
        .where(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            )
        )
        .values(is_read=True, read_at=datetime.utcnow())
    )
    await db.commit()
    
    return {"message": "All notifications marked as read"}


# 通知响应模型
from pydantic import BaseModel

class NotificationResponse(BaseModel):
    id: str
    title: str
    content: str
    notification_type: str
    level: str
    related_id: Optional[str]
    action_url: Optional[str]
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# 系统配置API
config_router = APIRouter(prefix="/config", tags=["系统配置"])


@config_router.get("")
async def list_configs(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取系统配置列表"""
    # 只有管理员可以看到所有配置
    if not current_user.is_superuser:
        # 普通用户只能看公开配置
        query = select(SystemConfig).where(SystemConfig.is_public == True)
    else:
        query = select(SystemConfig)
    
    if category:
        query = query.where(SystemConfig.category == category)
    
    result = await db.execute(query)
    configs = result.scalars().all()
    
    return [
        {
            "key": c.key,
            "value": c.value,
            "value_type": c.value_type,
            "description": c.description,
            "category": c.category,
            "is_public": c.is_public
        }
        for c in configs
    ]


@config_router.get("/{key}")
async def get_config(
    key: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个配置"""
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    # 检查权限
    if not config.is_public and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="No permission to view this config")
    
    return {
        "key": config.key,
        "value": config.value,
        "value_type": config.value_type,
        "description": config.description
    }


# 审计日志API
audit_router = APIRouter(prefix="/audit", tags=["审计日志"])


@audit_router.get("")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    resource: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取审计日志（仅管理员）"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin only")
    
    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    
    if action:
        query = query.where(AuditLog.action == action)
    if resource:
        query = query.where(AuditLog.resource == resource)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [AuditLogResponse.model_validate(l) for l in logs]


class AuditLogResponse(BaseModel):
    id: str
    action: str
    resource: str
    resource_id: Optional[str]
    method: Optional[str]
    path: Optional[str]
    ip_address: Optional[str]
    user_id: Optional[str]
    result: str
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True