"""API路由"""
from fastapi import APIRouter
from app.api import auth, users, business, templates, community, system, notifications

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(business.tasks_api, prefix="/tasks", tags=["任务管理"])
api_router.include_router(business.resources_api, prefix="/resources", tags=["资源管理"])
api_router.include_router(business.assets_api, prefix="/assets", tags=["资产管理"])
api_router.include_router(business.reports_api, prefix="/reports", tags=["评测报告"])
api_router.include_router(templates.router)
api_router.include_router(community.router)
api_router.include_router(system.router)
api_router.include_router(notifications.router)