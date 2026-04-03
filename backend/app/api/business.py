"""
核心业务API - 完整的评测平台API实现
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_, func
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User, UserRole, UserStatus
from app.models.task import EvaluationTask, TaskStatus, TaskPriority, EvaluationType, EvaluationTarget, TaskLog
from app.models.asset import Asset, ComputeResource, AssetType, AssetStatus
from app.models.report import Report, ReportType, ReportStatus, ReportSharing
from app.models.extended import Notification, NotificationType, SystemConfig


# ==================== 任务管理API ====================

tasks_api = APIRouter(prefix="/tasks", tags=["任务管理"])


@tasks_api.get("")
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    evaluation_type: Optional[EvaluationType] = None,
    evaluation_target: Optional[EvaluationTarget] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    query = select(EvaluationTask)
    
    # 权限过滤
    if not current_user.is_superuser:
        query = query.where(
            or_(
                EvaluationTask.user_id == current_user.id,
                EvaluationTask.tenant_id == current_user.tenant_id
            )
        )
    
    # 过滤条件
    if status:
        query = query.where(EvaluationTask.status == status)
    if evaluation_type:
        query = query.where(EvaluationTask.evaluation_type == evaluation_type)
    if evaluation_target:
        query = query.where(EvaluationTask.evaluation_target == evaluation_target)
    if search:
        query = query.where(EvaluationTask.name.contains(search))
    
    # 排序和分页
    query = query.order_by(desc(EvaluationTask.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # 获取总数
    count_query = select(func.count()).select_from(EvaluationTask)
    if not current_user.is_superuser:
        count_query = count_query.where(
            or_(
                EvaluationTask.user_id == current_user.id,
                EvaluationTask.tenant_id == current_user.tenant_id
            )
        )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return {
        "items": [TaskResponse.model_validate(t) for t in tasks],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@tasks_api.post("")
async def create_task(
    task_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建任务"""
    # 检查配额
    if current_user.tenant_id:
        from sqlalchemy import select
        result = await db.execute(
            select(func.count()).select_from(EvaluationTask).where(
                and_(
                    EvaluationTask.tenant_id == current_user.tenant_id,
                    EvaluationTask.status.in_([TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING])
                )
            )
        )
        active_count = result.scalar()
        
        # 获取租户配置
        from app.models.user import Tenant
        tenant_result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
        tenant = tenant_result.scalar_one_or_none()
        
        if tenant and active_count >= tenant.max_concurrent_tasks:
            raise HTTPException(
                status_code=400,
                detail=f"并发任务数已达上限 ({tenant.max_concurrent_tasks})"
            )
    
    # 创建任务
    task = EvaluationTask(
        id=str(uuid.uuid4()),
        name=task_data['name'],
        description=task_data.get('description'),
        evaluation_type=task_data['evaluation_type'],
        evaluation_target=task_data['evaluation_target'],
        priority=task_data.get('priority', TaskPriority.MEDIUM),
        required_gpu_count=task_data.get('required_gpu_count', 1),
        required_gpu_model=task_data.get('required_gpu_model'),
        required_memory_gb=task_data.get('required_memory_gb', 16),
        config=task_data.get('config'),
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        status=TaskStatus.PENDING,
    )
    
    # 判断是否收费
    if task_data.get('dataset_id') or task_data.get('tool_id') or task_data.get('required_gpu_model'):
        task.is_custom = True
        task.estimated_cost = task.required_gpu_count * 200
    
    db.add(task)
    
    # 添加日志
    log = TaskLog(
        id=str(uuid.uuid4()),
        task_id=task.id,
        level="INFO",
        message="Task created"
    )
    db.add(log)
    
    await db.commit()
    await db.refresh(task)
    
    return TaskResponse.model_validate(task)


@tasks_api.get("/{task_id}")
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情"""
    result = await db.execute(
        select(EvaluationTask).where(EvaluationTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 权限检查
    if (not current_user.is_superuser and 
        task.user_id != current_user.id and
        task.tenant_id != current_user.tenant_id):
        raise HTTPException(status_code=403, detail="No permission")
    
    return TaskResponse.model_validate(task)


@tasks_api.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除任务"""
    result = await db.execute(
        select(EvaluationTask).where(EvaluationTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 权限检查
    if not current_user.is_superuser and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission")
    
    # 只能删除已完成/失败/取消的任务
    if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Cannot delete active task")
    
    await db.delete(task)
    await db.commit()
    
    return {"message": "Task deleted"}


# 任务控制API
@tasks_api.post("/{task_id}/terminate")
async def terminate_task(
    task_id: str,
    force: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """终止任务"""
    result = await db.execute(
        select(EvaluationTask).where(EvaluationTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not current_user.is_superuser and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission")
    
    if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="Cannot terminate this task")
    
    task.status = TaskStatus.CANCELLED
    task.finished_at = datetime.utcnow()
    
    # 添加日志
    log = TaskLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        level="INFO",
        message=f"Task terminated (force={force})"
    )
    db.add(log)
    
    await db.commit()
    
    return {"status": "terminated", "task_id": task_id}


@tasks_api.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """重试任务"""
    result = await db.execute(
        select(EvaluationTask).where(EvaluationTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in [TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Cannot retry this task")
    
    task.status = TaskStatus.PENDING
    task.progress = 0.0
    task.started_at = None
    task.finished_at = None
    task.error_message = None
    
    # 添加日志
    log = TaskLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        level="INFO",
        message="Task retry initiated"
    )
    db.add(log)
    
    await db.commit()
    
    return {"status": "pending", "task_id": task_id}


@tasks_api.get("/{task_id}/logs")
async def get_task_logs(
    task_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务日志"""
    result = await db.execute(
        select(EvaluationTask).where(EvaluationTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 获取日志
    logs_result = await db.execute(
        select(TaskLog)
        .where(TaskLog.task_id == task_id)
        .order_by(desc(TaskLog.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = logs_result.scalars().all()
    
    return {
        "items": [TaskLogResponse.model_validate(l) for l in logs],
        "page": page,
        "page_size": page_size
    }


# ==================== 资源管理API ====================

resources_api = APIRouter(prefix="/resources", tags=["资源管理"])


@resources_api.get("")
async def list_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resource_type: Optional[str] = None,
    vendor: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取资源列表"""
    query = select(ComputeResource)
    
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
    
    # 统计
    stats_result = await db.execute(
        select(
            func.count().label('total'),
            func.sum(func.nullif(ComputeResource.gpu_count, 0)).label('total_gpu')
        ).where(ComputeResource.is_active == True)
    )
    stats = stats_result.first()
    
    return {
        "items": [ResourceResponse.model_validate(r) for r in resources],
        "stats": {
            "total": stats.total or 0,
            "total_gpu": stats.total_gpu or 0,
        },
        "page": page,
        "page_size": page_size
    }


@resources_api.get("/{resource_id}")
async def get_resource(
    resource_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取资源详情"""
    result = await db.execute(
        select(ComputeResource).where(ComputeResource.id == resource_id)
    )
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    return ResourceResponse.model_validate(resource)


@resources_api.get("/stats/summary")
async def get_resource_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取资源统计"""
    result = await db.execute(
        select(ComputeResource).where(ComputeResource.is_active == True)
    )
    resources = result.scalars().all()
    
    stats = {
        "total": len(resources),
        "available": 0,
        "busy": 0,
        "offline": 0,
        "total_gpu": 0,
        "vendors": {},
        "types": {}
    }
    
    for r in resources:
        stats[r.status] = stats.get(r.status, 0) + 1
        stats["total_gpu"] += r.gpu_count or 0
        stats["vendors"][r.vendor] = stats["vendors"].get(r.vendor, 0) + 1
        stats["types"][r.resource_type] = stats["types"].get(r.resource_type, 0) + 1
    
    return stats


# ==================== 资产API ====================

assets_api = APIRouter(prefix="/assets", tags=["资产管理"])


@assets_api.get("")
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    asset_type: Optional[AssetType] = None,
    is_public: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取资产列表"""
    query = select(Asset).where(Asset.status != AssetStatus.DELETED)
    
    # 权限过滤
    if not current_user.is_superuser:
        query = query.where(
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
        query = query.where(
            or_(
                Asset.name.contains(search),
                Asset.description.contains(search)
            )
        )
    
    query = query.order_by(desc(Asset.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    assets = result.scalars().all()
    
    return {
        "items": [AssetResponse.model_validate(a) for a in assets],
        "page": page,
        "page_size": page_size
    }


@assets_api.get("/{asset_id}")
async def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取资产详情"""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id)
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # 权限检查
    if (not asset.is_public and 
        asset.owner_id != current_user.id and
        not current_user.is_superuser and
        asset.tenant_id != current_user.tenant_id):
        raise HTTPException(status_code=403, detail="No permission")
    
    return AssetResponse.model_validate(asset)


# ==================== 报告API ====================

reports_api = APIRouter(prefix="/reports", tags=["评测报告"])


@reports_api.get("")
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    report_type: Optional[ReportType] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取报告列表"""
    query = select(Report)
    
    # 权限过滤
    if not current_user.is_superuser:
        query = query.where(
            or_(
                Report.user_id == current_user.id,
                Report.sharing == ReportSharing.PUBLIC,
                and_(Report.tenant_id == current_user.tenant_id, Report.sharing == ReportSharing.TENANT)
            )
        )
    
    if report_type:
        query = query.where(Report.report_type == report_type)
    
    query = query.order_by(desc(Report.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    return {
        "items": [ReportResponse.model_validate(r) for r in reports],
        "page": page,
        "page_size": page_size
    }


@reports_api.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取报告详情"""
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # 权限检查
    if (report.user_id != current_user.id and
        report.sharing == ReportSharing.PRIVATE and
        not current_user.is_superuser):
        raise HTTPException(status_code=403, detail="No permission")
    
    # 增加查看次数
    report.view_count += 1
    await db.commit()
    
    return ReportResponse.model_validate(report)


@reports_api.post("/generate/{task_id}")
async def generate_report(
    task_id: str,
    report_type: ReportType = ReportType.BASIC,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成报告"""
    # 获取任务
    task_result = await db.execute(
        select(EvaluationTask).where(EvaluationTask.id == task_id)
    )
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not completed")
    
    # 检查权限
    if task.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="No permission")
    
    # 检查是否已有报告
    existing = await db.execute(
        select(Report).where(Report.task_id == task_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Report already exists")
    
    # 创建报告
    report = Report(
        id=str(uuid.uuid4()),
        name=f"{task.name} - 评测报告",
        description=task.description,
        report_type=report_type,
        status=ReportStatus.READY,
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
    
    return ReportResponse.model_validate(report)


# 响应模型
from pydantic import BaseModel

class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    evaluation_type: str
    evaluation_target: str
    status: str
    priority: str
    progress: float
    required_gpu_count: int
    required_gpu_model: Optional[str]
    required_memory_gb: int
    allocated_resource_id: Optional[str]
    estimated_cost: int
    actual_cost: int
    error_message: Optional[str]
    user_id: str
    tenant_id: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TaskLogResponse(BaseModel):
    id: str
    task_id: str
    level: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ResourceResponse(BaseModel):
    id: str
    name: str
    resource_type: str
    vendor: str
    model: str
    gpu_count: int
    gpu_memory_gb: Optional[int]
    cpu_cores: Optional[int]
    cpu_memory_gb: Optional[int]
    status: str
    source: str
    price_per_hour: int
    total_usage_hours: float
    current_task_count: int
    
    class Config:
        from_attributes = True


class AssetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    asset_type: str
    status: str
    file_name: Optional[str]
    file_size: Optional[int]
    is_public: bool
    is_free: bool
    download_count: int
    owner_id: Optional[str]
    tenant_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    report_type: str
    status: str
    task_id: str
    user_id: str
    benchmark_score: Optional[float]
    benchmark_grade: Optional[str]
    sharing: str
    view_count: int
    download_count: int
    created_at: datetime
    generated_at: Optional[datetime]
    
    class Config:
        from_attributes = True