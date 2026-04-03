"""评测报告模型"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Enum as SQLEnum, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class ReportType(str, enum.Enum):
    """报告类型"""
    BASIC = "basic"        # 基础版
    ADVANCED = "advanced"  # 高级版
    DETAILED = "detailed"  # 详细版


class ReportStatus(str, enum.Enum):
    """报告状态"""
    GENERATING = "generating"  # 生成中
    READY = "ready"           # 就绪
    FAILED = "failed"         # 失败


class ReportSharing(str, enum.Enum):
    """分享范围"""
    PRIVATE = "private"       # 私有
    TENANT = "tenant"         # 租户内公开
    PUBLIC = "public"         # 公开


class Report(Base):
    """评测报告表"""
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    report_type = Column(SQLEnum(ReportType), default=ReportType.BASIC)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.GENERATING)
    
    # 报告内容
    summary = Column(JSON)          # 摘要
    metrics = Column(JSON)          # 指标数据
    charts = Column(JSON)           # 图表配置
    raw_data = Column(JSON)         # 原始数据
    analysis = Column(JSON)         # 分析结果
    
    # 基准对比
    benchmark_score = Column(Float) # 基准分
    benchmark_grade = Column(String(10))  # 等级 (A/B/C/D)
    rank = Column(Integer)          # 排名
    
    # 文件
    pdf_path = Column(String(512))  # PDF报告路径
    excel_path = Column(String(512))  # Excel报告路径
    
    # 分享设置
    sharing = Column(SQLEnum(ReportSharing), default=ReportSharing.PRIVATE)
    share_code = Column(String(36), unique=True)  # 分享码
    share_expires_at = Column(DateTime)  # 分享过期时间
    
    # 引用计数
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    
    # 任务关联
    task_id = Column(String(36), ForeignKey("evaluation_tasks.id"))
    
    # 所有者
    user_id = Column(String(36), ForeignKey("users.id"))
    tenant_id = Column(String(36), ForeignKey("tenants.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    generated_at = Column(DateTime)  # 生成完成时间
    
    # 关系
    task = relationship("EvaluationTask", backref="report")
    user = relationship("User", backref="reports")
    
    def __repr__(self):
        return f"<Report {self.name} ({self.status.value})>"


class ShareRecord(Base):
    """报告分享记录"""
    __tablename__ = "share_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False)
    
    # 分享信息
    shared_by = Column(String(36), ForeignKey("users.id"))  # 分享人
    shared_with = Column(String(255))  # 分享给（邮箱等）
    share_token = Column(String(64), unique=True)  # 分享令牌
    
    # 访问记录
    viewed_at = Column(DateTime)
    viewer_ip = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    def __repr__(self):
        return f"<ShareRecord {self.id}>"


class Member(Base):
    """租户成员表"""
    __tablename__ = "members"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    
    # 角色
    role = Column(String(50), default="member")  # owner, admin, member, guest
    
    # 状态
    status = Column(String(50), default="active")  # active, inactive, pending
    
    # 邀请
    invited_by = Column(String(36))
    invited_at = Column(DateTime)
    joined_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Member {self.user_id} in {self.tenant_id}>"


class ResourceAllocation(Base):
    """资源分配记录"""
    __tablename__ = "resource_allocations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 资源
    resource_id = Column(String(36), ForeignKey("compute_resources.id"), nullable=False)
    task_id = Column(String(36), ForeignKey("evaluation_tasks.id"))
    
    # 分配信息
    allocated_at = Column(DateTime, default=datetime.utcnow)
    released_at = Column(DateTime)
    
    # 使用统计
    gpu_hours = Column(Float, default=0)  # GPU使用时长
    memory_hours = Column(Float, default=0)  # 内存使用时长
    
    # 计费
    cost = Column(Integer, default=0)  # 费用（分）
    
    # 状态
    status = Column(String(50), default="allocated")  # allocated, released
    
    def __repr__(self):
        return f"<ResourceAllocation {self.id}>"


class Operator(Base):
    """算子表"""
    __tablename__ = "operators"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255))
    description = Column(Text)
    category = Column(String(50))  # 算子类别
    
    # 版本
    version = Column(String(50))
    framework = Column(String(50))  # 所属框架
    
    # 芯片支持
    chip_support = Column(JSON)  # 支持的芯片列表
    
    # 状态
    status = Column(String(50), default="verified")  # pending, verified, deprecated
    
    # 测试结果
    test_results = Column(JSON)  # 测试结果
    
    # 所有者
    owner_id = Column(String(36), ForeignKey("users.id"))
    tenant_id = Column(String(36), ForeignKey("tenants.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Operator {self.name}>"


class ReuseRecord(Base):
    """资产复用记录"""
    __tablename__ = "reuse_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 复用关系
    source_asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False)
    target_task_id = Column(String(36), ForeignKey("evaluation_tasks.id"))
    
    # 复用信息
    reused_by = Column(String(36), ForeignKey("users.id"))
    reuse_type = Column(String(50))  # dataset, model, tool
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ReuseRecord {self.id}>"