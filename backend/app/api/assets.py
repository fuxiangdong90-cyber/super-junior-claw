"""资产API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from datetime import datetime
import aiofiles
import hashlib
import os

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.models.asset import Asset, ComputeResource, AssetStatus
from app.schemas.asset import (
    AssetCreate, AssetUpdate, AssetResponse,
    ComputeResourceCreate, ComputeResourceUpdate, ComputeResourceResponse
)

router = APIRouter(tags=["资产管理"])

# 上传目录
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============== 资产 API ==============

@router.post("/assets", response_model=AssetResponse)
async def create_asset(
    asset_data: AssetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建资产记录"""
    asset = Asset(
        name=asset_data.name,
        description=asset_data.description,
        asset_type=asset_data.asset_type,
        tags=asset_data.tags,
        is_public=asset_data.is_public,
        is_free=asset_data.is_free,
        file_name=asset_data.file_name,
        file_size=asset_data.file_size,
        mime_type=asset_data.mime_type,
        status=AssetStatus.READY,
        owner_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    
    return AssetResponse.model_validate(asset)


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    asset_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取资产列表"""
    # 公开资产 或 用户自己创建的资产
    query = select(Asset).where(
        or_(
            Asset.is_public == True,
            Asset.owner_id == current_user.id,
            Asset.tenant_id == current_user.tenant_id
        )
    )
    
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)
    if is_public is not None:
        query = query.where(Asset.is_public == is_public)
    if search:
        query = query.where(Asset.name.contains(search) | Asset.description.contains(search))
    
    query = query.order_by(desc(Asset.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    assets = result.scalars().all()
    
    return [AssetResponse.model_validate(a) for a in assets]


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取资产详情"""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # 检查权限
    if not asset.is_public and asset.owner_id != current_user.id:
        if not current_user.is_superuser and asset.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to access this asset"
            )
    
    return AssetResponse.model_validate(asset)


@router.patch("/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    asset_data: AssetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新资产"""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # 检查权限
    if asset.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to update this asset"
        )
    
    # 更新字段
    update_data = asset_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    
    await db.commit()
    await db.refresh(asset)
    
    return AssetResponse.model_validate(asset)


# ============== 算力资源 API ==============

@router.post("/resources", response_model=ComputeResourceResponse)
async def create_resource(
    resource_data: ComputeResourceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建算力资源"""
    # 检查权限（需要管理员）
    if current_user.role.value not in ["admin", "tenant_admin"] and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to create resources"
        )
    
    resource = ComputeResource(
        name=resource_data.name,
        description=resource_data.description,
        resource_type=resource_data.resource_type,
        vendor=resource_data.vendor,
        model=resource_data.model,
        gpu_count=resource_data.gpu_count,
        gpu_memory_gb=resource_data.gpu_memory_gb,
        cpu_cores=resource_data.cpu_cores,
        cpu_memory_gb=resource_data.cpu_memory_gb,
        storage_tb=resource_data.storage_tb,
        source=resource_data.source,
        price_per_hour=resource_data.price_per_hour,
        cloud_provider=resource_data.cloud_provider,
        cloud_region=resource_data.cloud_region,
        cloud_instance_id=resource_data.cloud_instance_id,
        tenant_id=current_user.tenant_id,
    )
    
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    
    return ComputeResourceResponse.model_validate(resource)


@router.get("/resources", response_model=List[ComputeResourceResponse])
async def list_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resource_type: Optional[str] = None,
    vendor: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取算力资源列表"""
    query = select(ComputeResource).where(ComputeResource.is_active == True)
    
    if resource_type:
        query = query.where(ComputeResource.resource_type == resource_type)
    if vendor:
        query = query.where(ComputeResource.vendor == vendor)
    if status:
        query = query.where(ComputeResource.status == status)
    
    query = query.order_by(ComputeResource.name)
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    resources = result.scalars().all()
    
    return [ComputeResourceResponse.model_validate(r) for r in resources]


@router.get("/resources/{resource_id}", response_model=ComputeResourceResponse)
async def get_resource(
    resource_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取算力资源详情"""
    result = await db.execute(select(ComputeResource).where(ComputeResource.id == resource_id))
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    return ComputeResourceResponse.model_validate(resource)