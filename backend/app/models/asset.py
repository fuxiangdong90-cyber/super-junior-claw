"""资产管理模型"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Enum as SQLEnum, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class AssetType(str, enum.Enum):
    """资产类型"""
    DATASET = "dataset"           # 数据集
    MODEL = "model"               # 模型文件
    FRAMEWORK = "framework"       # 框架
    TOOL = "tool"                 # 评测工具
    REPORT = "report"             # 评测报告
    IMAGE = "image"               # 镜像


class AssetStatus(str, enum.Enum):
    """资产状态"""
    UPLOADING = "uploading"       # 上传中
    READY = "ready"               # 就绪
    PROCESSING = "processing"     # 处理中
    FAILED = "failed"             # 失败
    DELETED = "deleted"           # 已删除


class Asset(Base):
    """资产表"""
    __tablename__ = "assets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    asset_type = Column(SQLEnum(AssetType), nullable=False)
    status = Column(SQLEnum(AssetStatus), default=AssetStatus.UPLOADING)
    
    # 文件信息
    file_name = Column(String(255))
    file_size = Column(Integer)  # bytes
    file_path = Column(String(512))  # 存储路径
    mime_type = Column(String(100))
    checksum = Column(String(64))  # SHA256
    
    # 元数据
    metadata = Column(JSON)
    tags = Column(JSON)  # ["image classification", "vision"]
    
    # 引用计数
    reference_count = Column(Integer, default=0)
    
    # 访问控制
    is_public = Column(Boolean, default=False)  # 公开资源（社区）
    is_free = Column(Boolean, default=False)    # 免费资源
    download_count = Column(Integer, default=0)
    
    # 所有者
    owner_id = Column(String(36), ForeignKey("users.id"))
    tenant_id = Column(String(36), ForeignKey("tenants.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    owner = relationship("User", back_populates="assets")
    tenant = relationship("Tenant", back_populates="assets")
    
    def __repr__(self):
        return f"<Asset {self.name} ({self.asset_type.value})>"


class ComputeResource(Base):
    """算力资源表"""
    __tablename__ = "compute_resources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # 资源类型
    resource_type = Column(String(50))  # gpu, cpu, fpga, npu
    vendor = Column(String(100))  # 厂商: 华为, 寒武纪, 摩尔线程等
    model = Column(String(100))  # 型号: Ascend-910, Kunlun-910
    
    # 资源配置
    gpu_count = Column(Integer, default=1)
    gpu_memory_gb = Column(Integer)
    cpu_cores = Column(Integer)
    cpu_memory_gb = Column(Integer)
    storage_tb = Column(Float)
    
    # 资源来源
    source = Column(String(50))  # self: 平台自有, cloud: 云厂商, user: 用户自有
    
    # 云厂商信息（如果是云资源）
    cloud_provider = Column(String(50))
    cloud_region = Column(String(50))
    cloud_instance_id = Column(String(100))
    
    # 状态
    status = Column(String(50), default="available")  # available, busy, offline, maintenance
    is_active = Column(Boolean, default=True)
    
    # 使用统计
    total_usage_hours = Column(Float, default=0)
    current_task_count = Column(Integer, default=0)
    
    # 关联租户
    tenant_id = Column(String(36), ForeignKey("tenants.id"))
    
    # 价格（每小时，分解）
    price_per_hour = Column(Integer, default=0)  # 分
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ComputeResource {self.name} ({self.model})>"