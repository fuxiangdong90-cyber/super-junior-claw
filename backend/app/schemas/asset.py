"""资产Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.asset import AssetType, AssetStatus


class AssetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: AssetType
    tags: Optional[List[str]] = None
    is_public: bool = False
    is_free: bool = False


class AssetCreate(AssetBase):
    """创建资产"""
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class AssetUpdate(BaseModel):
    """更新资产"""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    is_free: Optional[bool] = None
    status: Optional[AssetStatus] = None


class AssetResponse(AssetBase):
    """资产响应"""
    id: str
    status: AssetStatus
    
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    
    metadata: Optional[dict] = None
    reference_count: int
    download_count: int
    
    owner_id: Optional[str] = None
    tenant_id: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Compute Resource Schemas
class ComputeResourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    resource_type: str  # gpu, cpu, fpga, npu
    vendor: str  # 华为, 寒武纪, 摩尔线程
    model: str  # Ascend-910, Kunlun-910
    
    gpu_count: int = 1
    gpu_memory_gb: Optional[int] = None
    cpu_cores: Optional[int] = None
    cpu_memory_gb: Optional[int] = None
    storage_tb: Optional[float] = None
    
    source: str = "self"  # self, cloud, user
    price_per_hour: int = 0  # 分


class ComputeResourceCreate(ComputeResourceBase):
    """创建算力资源"""
    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None
    cloud_instance_id: Optional[str] = None


class ComputeResourceUpdate(BaseModel):
    """更新算力资源"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    price_per_hour: Optional[int] = None


class ComputeResourceResponse(ComputeResourceBase):
    """算力资源响应"""
    id: str
    status: str
    is_active: bool
    total_usage_hours: float
    current_task_count: int
    tenant_id: Optional[str] = None
    cloud_provider: Optional[str] = None
    cloud_region: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True