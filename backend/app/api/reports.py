"""报告API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from datetime import datetime, timedelta
import uuid
import secrets

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.task import EvaluationTask
from app.models.report import Report, ReportType, ReportStatus, ReportSharing, ShareRecord

router = APIRouter(prefix="/reports", tags=["评测报告"])


@router.get("")
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    report_type: Optional[ReportType] = None,
    status: Optional[ReportStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取报告列表"""
    query = select(Report)
    
    # 权限过滤：自己的报告 + 公开的报告 + 租户内的报告
    query = query.where(
        or_(
            Report.user_id == current_user.id,
            Report.sharing == ReportSharing.PUBLIC,
            and_(Report.tenant_id == current_user.tenant_id, Report.sharing == ReportSharing.TENANT)
        )
    )
    
    if report_type:
        query = query.where(Report.report_type == report_type)
    if status:
        query = query.where(Report.status == status)
    
    query = query.order_by(desc(Report.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    # 获取总数
    count_query = select(Report).where(
        or_(
            Report.user_id == current_user.id,
            Report.sharing == ReportSharing.PUBLIC,
            and_(Report.tenant_id == current_user.tenant_id, Report.sharing == ReportSharing.TENANT)
        )
    )
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())
    
    return {
        "items": [ReportResponse.model_validate(r) for r in reports],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    share_code: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取报告详情"""
    # 如果提供了分享码
    if share_code:
        result = await db.execute(
            select(Report).where(Report.share_code == share_code)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # 检查分享码是否过期
        if report.share_expires_at and report.share_expires_at < datetime.utcnow():
            raise HTTPException(status_code=410, detail="Share link expired")
        
        # 增加查看次数
        report.view_count += 1
        await db.commit()
        
        return ReportResponse.model_validate(report)
    
    # 正常访问
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # 检查权限
    if (report.user_id != current_user.id and 
        report.sharing == ReportSharing.PRIVATE and
        report.tenant_id != current_user.tenant_id):
        raise HTTPException(status_code=403, detail="No permission to view this report")
    
    # 增加查看次数
    report.view_count += 1
    await db.commit()
    
    return ReportResponse.model_validate(report)


@router.post("")
async def create_report(
    task_id: str,
    report_type: ReportType = ReportType.BASIC,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建报告（基于任务结果生成）"""
    # 获取任务
    result = await db.execute(
        select(EvaluationTask).where(
            and_(EvaluationTask.id == task_id, EvaluationTask.user_id == current_user.id)
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
    
    # 创建报告
    report = Report(
        name=f"{task.name} - 评测报告",
        description=task.description,
        report_type=report_type,
        status=ReportStatus.GENERATING,
        task_id=task_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        summary=task.result,
        metrics=task.result.get('metrics') if task.result else None,
    )
    
    # 生成基准分数
    if task.result and 'benchmark' in task.result:
        report.benchmark_score = task.result['benchmark'].get('score', 0)
        report.benchmark_grade = task.result['benchmark'].get('grade', 'C')
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # TODO: 异步生成报告详情
    report.status = ReportStatus.READY
    report.generated_at = datetime.utcnow()
    await db.commit()
    
    return ReportResponse.model_validate(report)


@router.post("/{report_id}/share")
async def share_report(
    report_id: str,
    expires_hours: int = 24,
    sharing: ReportSharing = ReportSharing.PRIVATE,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """分享报告"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission to share this report")
    
    # 生成分享码
    share_code = secrets.token_urlsafe(16)
    report.share_code = share_code
    report.sharing = sharing
    report.share_expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    
    await db.commit()
    
    return {
        "share_url": f"/reports/shared/{share_code}",
        "expires_at": report.share_expires_at.isoformat(),
        "sharing": sharing.value
    }


@router.get("/shared/{share_code}")
async def get_shared_report(
    share_code: str,
    db: AsyncSession = Depends(get_db)
):
    """通过分享码访问报告"""
    result = await db.execute(
        select(Report).where(Report.share_code == share_code)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.share_expires_at and report.share_expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Share link expired")
    
    # 增加查看次数
    report.view_count += 1
    await db.commit()
    
    return ReportResponse.model_validate(report)


@router.post("/generate")
async def generate_report(
    task_id: str,
    report_type: ReportType = ReportType.ADVANCED,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成报告（异步）"""
    # 获取任务
    result = await db.execute(
        select(EvaluationTask).where(
            and_(EvaluationTask.id == task_id, EvaluationTask.user_id == current_user.id)
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 创建报告记录
    report = Report(
        name=f"{task.name} - 评测报告",
        report_type=report_type,
        status=ReportStatus.GENERATING,
        task_id=task_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    # TODO: 触发异步报告生成任务
    
    return {
        "report_id": report.id,
        "status": "generating",
        "message": "Report generation started"
    }


# 响应模型
from pydantic import BaseModel

class ReportResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    report_type: ReportType
    status: ReportStatus
    
    summary: Optional[dict]
    metrics: Optional[dict]
    charts: Optional[dict]
    
    benchmark_score: Optional[float]
    benchmark_grade: Optional[str]
    rank: Optional[int]
    
    sharing: ReportSharing
    view_count: int
    download_count: int
    share_count: int
    
    task_id: str
    user_id: str
    tenant_id: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    generated_at: Optional[datetime]
    
    class Config:
        from_attributes = True