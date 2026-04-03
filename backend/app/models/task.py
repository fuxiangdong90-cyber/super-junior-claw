"""评测任务模型"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Enum as SQLEnum, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    """任务状态"""
    PENDING = "pending"           # 待执行
    QUEUED = "queued"             # 排队中
    RUNNING = "running"           # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消
    PAUSED = "paused"             # 暂停


class TaskPriority(str, enum.Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EvaluationType(str, enum.Enum):
    """评测类型"""
    PERFORMANCE = "performance"   # 性能评测
    PRECISION = "precision"       # 精度评测
    COMPATIBILITY = "compatibility"  # 兼容性评测
    STABILITY = "stability"       # 稳定性评测


class EvaluationTarget(str, enum.Enum):
    """评测对象"""
    CHIP = "chip"                 # 芯片
    OPERATOR = "operator"         # 算子
    FRAMEWORK = "framework"       # 框架
    MODEL = "model"               # 模型
    SCENARIO = "scenario"         # 场景


class EvaluationTask(Base):
    """评测任务表"""
    __tablename__ = "evaluation_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # 任务类型与对象
    evaluation_type = Column(SQLEnum(EvaluationType), nullable=False)
    evaluation_target = Column(SQLEnum(EvaluationTarget), nullable=False)
    
    # 任务状态
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    progress = Column(Float, default=0.0)  # 0-100
    
    # 任务配置
    config = Column(JSON)  # 评测参数配置
    result = Column(JSON)  # 评测结果
    
    # 资源配置
    required_gpu_count = Column(Integer, default=1)
    required_gpu_model = Column(String(100))  # 如 "Ascend-910", "Kunlun-910"
    required_memory_gb = Column(Integer, default=16)
    
    # 资源分配
    allocated_resource_id = Column(String(36))  # 分配的算力资源ID
    
    # 队列信息
    queue_position = Column(Integer, default=0)
    estimated_start_time = Column(DateTime)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    
    # 计费
    is_custom = Column(Boolean, default=False)  # 是否自定义评测（收费）
    estimated_cost = Column(Integer, default=0)  # 预估费用（分）
    actual_cost = Column(Integer, default=0)     # 实际费用（分）
    
    # 错误信息
    error_message = Column(Text)
    error_detail = Column(JSON)
    
    # 外键
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"))
    
    # 数据集与工具
    dataset_id = Column(String(36))
    tool_id = Column(String(36))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="evaluation_tasks")
    tenant = relationship("Tenant", back_populates="evaluation_tasks")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EvaluationTask {self.name} ({self.status.value})>"


class TaskLog(Base):
    """任务日志表"""
    __tablename__ = "task_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("evaluation_tasks.id"), nullable=False)
    level = Column(String(20))  # INFO, WARNING, ERROR
    message = Column(Text)
    data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    task = relationship("EvaluationTask", back_populates="logs")
    
    def __repr__(self):
        return f"<TaskLog {self.level}: {self.message[:50]}>"