"""评测执行服务 - Celery任务"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# 创建Celery应用
celery_app = Celery(
    "ai_validation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.services.evaluation",
        "app.services.scheduler",
    ]
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600 * 24,  # 24小时最大执行时间
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    # 清理过期任务
    "cleanup-expired-tasks": {
        "task": "app.services.scheduler.cleanup_expired_tasks",
        "schedule": crontab(hour=3, minute=0),  # 每天凌晨3点
    },
    # 检查资源健康
    "check-resources-health": {
        "task": "app.services.scheduler.check_resources_health",
        "schedule": 300,  # 每5分钟
    },
    # 生成报表
    "generate-daily-report": {
        "task": "app.services.scheduler.generate_daily_report",
        "schedule": crontab(hour=0, minute=5),  # 每天凌晨0:05
    },
}