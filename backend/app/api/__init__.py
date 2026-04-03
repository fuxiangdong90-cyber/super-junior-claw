"""API路由"""
from fastapi import APIRouter
from app.api import auth, tasks, assets, billing, community, system, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(tasks.router)
api_router.include_router(assets.router)
api_router.include_router(billing.router)
api_router.include_router(community.router)
api_router.include_router(system.router)