"""任务调度服务"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from celery import Celery

from app.services.celery_app import celery_app
from app.models.task import EvaluationTask, TaskStatus, TaskPriority
from app.models.asset import ComputeResource
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, and_, or_


@celery_app.task(bind=True, name="app.services.scheduler.schedule_tasks")
def schedule_tasks(self):
    """调度待执行的任务"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_schedule_tasks_internal())


async def _schedule_tasks_internal():
    """实际的任务调度逻辑"""
    async with AsyncSessionLocal() as db:
        # 获取所有待执行和排队的任务
        result = await db.execute(
            select(EvaluationTask)
            .where(
                or_(
                    EvaluationTask.status == TaskStatus.PENDING,
                    EvaluationTask.status == TaskStatus.QUEUED
                )
            )
            .order_by(
                EvaluationTask.priority.desc(),
                EvaluationTask.created_at
            )
        )
        tasks = result.scalars().all()
        
        scheduled = []
        for task in tasks:
            # 尝试分配资源
            resource = await _allocate_resource(task, db)
            
            if resource:
                # 分配到资源，执行任务
                task.status = TaskStatus.RUNNING
                task.allocated_resource_id = resource.id
                task.started_at = datetime.utcnow()
                
                # 更新资源状态
                resource.status = "busy"
                resource.current_task_count += 1
                
                # 触发执行
                from app.services.evaluation import execute_evaluation
                execute_evaluation.delay(task.id)
                
                scheduled.append(task.id)
        
        await db.commit()
        return {"scheduled": scheduled}


async def _allocate_resource(task: EvaluationTask, db: AsyncSession) -> Optional[ComputeResource]:
    """为任务分配资源"""
    # 查询可用资源
    query = select(ComputeResource).where(
        and_(
            ComputeResource.status == "available",
            ComputeResource.is_active == True,
            ComputeResource.gpu_count >= task.required_gpu_count
        )
    )
    
    # 如果指定了GPU型号
    if task.required_gpu_model:
        query = query.where(ComputeResource.model == task.required_gpu_model)
    
    result = await db.execute(query.limit(1))
    return result.scalar_one_or_none()


@celery_app.task(name="app.services.scheduler.cleanup_expired_tasks")
def cleanup_expired_tasks():
    """清理过期任务"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_cleanup_expired_tasks_internal())


async def _cleanup_expired_tasks_internal():
    """清理过期的失败/取消任务"""
    async with AsyncSessionLocal() as db:
        # 清理30天前的已取消和失败任务
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        result = await db.execute(
            select(EvaluationTask).where(
                and_(
                    EvaluationTask.created_at < cutoff,
                    or_(
                        EvaluationTask.status == TaskStatus.CANCELLED,
                        EvaluationTask.status == TaskStatus.FAILED
                    )
                )
            )
        )
        tasks = result.scalars().all()
        
        deleted_count = 0
        for task in tasks:
            await db.delete(task)
            deleted_count += 1
        
        await db.commit()
        return {"deleted_count": deleted_count}


@celery_app.task(name="app.services.scheduler.check_resources_health")
def check_resources_health():
    """检查资源健康状态"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_check_resources_health_internal())


async def _check_resources_health_internal():
    """检查所有资源的状态"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ComputeResource).where(ComputeResource.is_active == True)
        )
        resources = result.scalars().all()
        
        health_report = []
        for resource in resources:
            # 简化：检查资源是否超时未更新
            time_since_update = datetime.utcnow() - resource.updated_at
            
            if time_since_update > timedelta(hours=1) and resource.status == "busy":
                # 标记为可能离线
                health_report.append({
                    "resource_id": resource.id,
                    "status": "suspected_offline",
                    "last_update": resource.updated_at.isoformat()
                })
        
        return {"health_report": health_report}


@celery_app.task(name="app.services.scheduler.generate_daily_report")
def generate_daily_report():
    """生成日报"""
    # 实际应生成更详细的报表
    return {
        "date": datetime.utcnow().date().isoformat(),
        "total_tasks": 0,
        "completed_tasks": 0,
        "failed_tasks": 0,
    }


@celery_app.task(name="app.services.scheduler.rebalance_resources")
def rebalance_resources():
    """资源再平衡"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_rebalance_resources_internal())


async def _rebalance_resources_internal():
    """平衡资源负载"""
    async with AsyncSessionLocal() as db:
        # 获取所有忙碌的资源
        result = await db.execute(
            select(ComputeResource).where(ComputeResource.status == "busy")
        )
        resources = result.scalars().all()
        
        rebalanced = []
        for resource in resources:
            # 检查是否有过多任务
            if resource.current_task_count > 2:
                # 尝试重新分配
                pass
        
        return {"rebalanced": rebalanced}