"""服务模块"""
from app.services.celery_app import celery_app
from app.services import evaluation, scheduler

__all__ = [
    "celery_app",
    "evaluation",
    "scheduler",
]