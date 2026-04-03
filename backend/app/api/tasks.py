"""评测任务API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.task import EvaluationTask, TaskStatus, TaskPriority
from app.schemas.task import (
    EvaluationTaskCreate, EvaluationTaskUpdate,
    EvaluationTaskResponse, TaskLogResponse
)

router = APIRouter(prefix="/tasks", tags=["评测任务"])


@router.post("", response_model=EvaluationTaskResponse)
async def create_task(
    task_data: EvaluationTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建评测任务"""
    # 创建任务
    task = EvaluationTask(
        name=task_data.name,
        description=task_data.description,
        evaluation_type=task_data.evaluation_type,
        evaluation_target=task_data.evaluation_target,
        priority=task_data.priority,
        required_gpu_count=task_data.required_gpu_count,
        required_gpu_model=task_data.required_gpu_model,
        required_memory_gb=task_data.required_memory_gb,
        config=task_data.config.model_dump() if task_data.config else None,
        dataset_id=task_data.dataset_id,
        tool_id=task_data.tool_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        status=TaskStatus.PENDING,
    )
    
    # 判断是否为自定义评测（收费）
    if task_data.dataset_id or task_data.tool_id or task_data.required_gpu_model:
        task.is_custom = True
        # 预估费用（简化计算）
        task.estimated_cost = task_data.required_gpu_count * 100  # 假设每小时100分
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return EvaluationTaskResponse.model_validate(task)


@router.get("", response_model=List[EvaluationTaskResponse])
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[TaskStatus] = None,
    evaluation_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取评测任务列表"""
    query = select(EvaluationTask).where(EvaluationTask.user_id == current_user.id)
    
    if status_filter:
        query = query.where(EvaluationTask.status == status_filter)
    if evaluation_type:
        query = query.where(EvaluationTask.evaluation_type == evaluation_type)
    
    query = query.order_by(desc(EvaluationTask.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return [EvaluationTaskResponse.model_validate(t) for t in tasks]


@router.get("/{task_id}", response_model=EvaluationTaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取评测任务详情"""
    result = await db.execute(
        select(EvaluationTask).where(
            and_(
                EvaluationTask.id == task_id,
                EvaluationTask.user_id == current_user.id
            )
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return EvaluationTaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=EvaluationTaskResponse)
async def update_task(
    task_id: str,
    task_data: EvaluationTaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新评测任务"""
    result = await db.execute(
        select(EvaluationTask).where(
            and_(
                EvaluationTask.id == task_id,
                EvaluationTask.user_id == current_user.id
            )
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 只能更新特定字段
    if task_data.name is not None:
        task.name = task_data.name
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.status is not None:
        # 只能取消进行中的任务
        if task_data.status == TaskStatus.CANCELLED and task.status in [
            TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING
        ]:
            task.status = TaskStatus.CANCELLED
    
    await db.commit()
    await db.refresh(task)
    
    return EvaluationTaskResponse.model_validate(task)


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除评测任务"""
    result = await db.execute(
        select(EvaluationTask).where(
            and_(
                EvaluationTask.id == task_id,
                EvaluationTask.user_id == current_user.id
            )
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 只能删除已完成或失败的任务
    if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete completed, failed or cancelled tasks"
        )
    
    await db.delete(task)
    await db.commit()
    
    return {"message": "Task deleted successfully"}


@router.get("/{task_id}/logs", response_model=List[TaskLogResponse])
async def get_task_logs(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务日志"""
    # 先验证任务存在且属于当前用户
    task_result = await db.execute(
        select(EvaluationTask).where(
            and_(
                EvaluationTask.id == task_id,
                EvaluationTask.user_id == current_user.id
            )
        )
    )
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 获取日志
    result = await db.execute(
        select(TaskLog)
        .where(TaskLog.task_id == task_id)
        .order_by(desc(TaskLog.created_at))
        .limit(100)
    )
    logs = result.scalars().all()
    
    return [TaskLogResponse.model_validate(log) for log in logs]