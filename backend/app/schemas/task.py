"""评测任务Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority, EvaluationType, EvaluationTarget


class TaskConfig(BaseModel):
    """任务配置"""
    dataset_id: Optional[str] = None
    tool_id: Optional[str] = None
    custom_params: Optional[dict] = None
    timeout_hours: Optional[int] = 24


class EvaluationTaskBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    evaluation_type: EvaluationType
    evaluation_target: EvaluationTarget
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # 资源配置
    required_gpu_count: int = 1
    required_gpu_model: Optional[str] = None
    required_memory_gb: int = 16
    
    # 任务配置
    config: Optional[TaskConfig] = None
    
    # 数据集与工具
    dataset_id: Optional[str] = None
    tool_id: Optional[str] = None


class EvaluationTaskCreate(EvaluationTaskBase):
    """创建评测任务"""
    pass


class EvaluationTaskUpdate(BaseModel):
    """更新评测任务"""
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None


class EvaluationTaskResponse(EvaluationTaskBase):
    """评测任务响应"""
    id: str
    status: TaskStatus
    priority: TaskPriority
    progress: float
    result: Optional[dict] = None
    allocated_resource_id: Optional[str] = None
    queue_position: int
    estimated_start_time: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    # 计费
    is_custom: bool
    estimated_cost: int
    actual_cost: int
    
    # 错误
    error_message: Optional[str] = None
    
    user_id: str
    tenant_id: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskLogResponse(BaseModel):
    """任务日志响应"""
    id: str
    task_id: str
    level: str
    message: str
    data: Optional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# 模板
class TaskTemplate(BaseModel):
    """评测任务模板"""
    id: str
    name: str
    description: str
    evaluation_type: EvaluationType
    evaluation_target: EvaluationTarget
    default_config: dict
    is_free: bool = True