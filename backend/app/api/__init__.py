"""API路由"""
from fastapi import APIRouter
from app.api import auth, tasks, assets, billing, community, system, users, templates, reports, task_control

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(tasks.router)
api_router.include_router(task_control.router)
api_router.include_router(assets.router)
api_router.include_router(reports.router)
api_router.include_router(billing.router)
api_router.include_router(community.router)
api_router.include_router(templates.router)
api_router.include_router(system.router)