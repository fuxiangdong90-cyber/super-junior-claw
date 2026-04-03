"""任务控制API - 任务终止/重试/资源管理"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.task import EvaluationTask, TaskStatus, TaskPriority, TaskLog
from app.models.report import Report, ReportType

router = APIRouter(prefix="/tasks", tags=["任务控制"])


@router.post("/{task_id}/terminate")
async def terminate_task(
    task_id: str,
    force: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """终止任务"""
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
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot terminate task in status: {task.status.value}"
        )
    
    # 更新任务状态
    task.status = TaskStatus.CANCELLED
    task.finished_at = datetime.utcnow()
    
    # 添加日志
    log = TaskLog(
        task_id=task_id,
        level="INFO",
        message=f"Task terminated by user (force={force})"
    )
    db.add(log)
    
    # 释放资源
    if task.allocated_resource_id:
        # TODO: 调用资源释放
        pass
    
    await db.commit()
    
    return {
        "task_id": task_id,
        "status": "terminated",
        "message": "Task terminated successfully"
    }


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """重试任务"""
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
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in [TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry task in status: {task.status.value}"
        )
    
    # 重置任务状态
    task.status = TaskStatus.PENDING
    task.progress = 0.0
    task.started_at = None
    task.finished_at = None
    task.error_message = None
    task.allocated_resource_id = None
    
    # 添加日志
    log = TaskLog(
        task_id=task_id,
        level="INFO",
        message="Task retry initiated by user"
    )
    db.add(log)
    
    await db.commit()
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Task queued for retry"
    }


@router.post("/{task_id}/pause")
async def pause_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """暂停任务"""
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
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Only running tasks can be paused")
    
    # 暂停任务
    task.status = TaskStatus.PAUSED
    
    # 添加日志
    log = TaskLog(
        task_id=task_id,
        level="INFO",
        message="Task paused by user"
    )
    db.add(log)
    
    await db.commit()
    
    return {
        "task_id": task_id,
        "status": "paused",
        "message": "Task paused successfully"
    }


@router.post("/{task_id}/resume")
async def resume_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """恢复任务"""
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
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Only paused tasks can be resumed")
    
    # 恢复任务
    task.status = TaskStatus.RUNNING
    
    # 添加日志
    log = TaskLog(
        task_id=task_id,
        level="INFO",
        message="Task resumed by user"
    )
    db.add(log)
    
    await db.commit()
    
    return {
        "task_id": task_id,
        "status": "running",
        "message": "Task resumed successfully"
    }


@router.get("/{task_id}/progress")
async def get_task_progress(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务进度详情"""
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
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 获取任务日志
    logs_result = await db.execute(
        select(TaskLog)
        .where(TaskLog.task_id == task_id)
        .order_by(desc(TaskLog.created_at))
        .limit(50)
    )
    logs = logs_result.scalars().all()
    
    # 计算耗时
    elapsed_time = None
    estimated_remaining = None
    
    if task.started_at:
        elapsed = datetime.utcnow() - task.started_at
        elapsed_time = elapsed.total_seconds()
        
        if task.progress > 0:
            estimated_total = elapsed_time / (task.progress / 100)
            estimated_remaining = estimated_total - elapsed_time
    
    return {
        "task_id": task_id,
        "name": task.name,
        "status": task.status.value,
        "progress": task.progress,
        "elapsed_seconds": elapsed_time,
        "estimated_remaining_seconds": estimated_remaining,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
        "error_message": task.error_message,
        "logs": [
            {
                "level": log.level,
                "message": log.message,
                "timestamp": log.created_at.isoformat()
            }
            for log in logs
        ]
    }


@router.post("/{task_id}/report")
async def generate_task_report(
    task_id: str,
    report_type: ReportType = ReportType.BASIC,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成任务报告"""
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
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not completed")
    
    # 检查是否已有报告
    existing = await db.execute(
        select(Report).where(Report.task_id == task_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Report already exists for this task")
    
    # 创建报告
    from app.models.report import Report as ReportModel, ReportStatus as ReportStatusModel
    
    report = ReportModel(
        name=f"{task.name} - 评测报告",
        description=task.description,
        report_type=report_type,
        status=ReportStatusModel.READY,
        task_id=task_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        summary=task.result,
        metrics=task.result.get('metrics') if task.result else None,
        generated_at=datetime.utcnow(),
    )
    
    if task.result and 'benchmark' in task.result:
        report.benchmark_score = task.result['benchmark'].get('score', 0)
        report.benchmark_grade = task.result['benchmark'].get('grade', 'C')
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return {
        "report_id": report.id,
        "status": "generated",
        "message": "Report generated successfully"
    }