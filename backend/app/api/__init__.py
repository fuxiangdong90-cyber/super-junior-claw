"""API路由"""
from fastapi import APIRouter
from app.api import auth, tasks, assets

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(tasks.router)
api_router.include_router(assets.router)