"""社区服务API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.asset import Asset
from app.schemas.community import (
    PostCreate, PostResponse, CommentResponse,
    CategoryResponse, TagResponse
)

router = APIRouter(prefix="/community", tags=["社区"])


# 模拟数据（实际应从数据库读取）
CATEGORIES = [
    {"id": "1", "name": "芯片评测", "description": "国产芯片评测讨论", "post_count": 120},
    {"id": "2", "name": "框架适配", "description": "AI框架适配经验", "post_count": 85},
    {"id": "3", "name": "模型部署", "description": "模型部署与优化", "post_count": 200},
    {"id": "4", "name": "算力资源", "description": "算力资源共享", "post_count": 60},
    {"id": "5", "name": "技术问答", "description": "技术问题交流", "post_count": 350},
]


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories():
    """获取社区分类"""
    return CATEGORIES


@router.get("/posts", response_model=List[PostResponse])
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    category_id: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取帖子列表"""
    # 简化实现：返回公开的资产作为社区资源
    query = select(Asset).where(
        and_(
            Asset.is_public == True,
            Asset.status == "ready"
        )
    )
    
    if category_id:
        query = query.where(Asset.asset_type == category_id)
    if tag:
        query = query.where(Asset.tags.contains([tag]))
    
    query = query.order_by(desc(Asset.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    assets = result.scalars().all()
    
    # 转换为帖子格式
    posts = []
    for asset in assets:
        posts.append(PostResponse(
            id=asset.id,
            title=asset.name,
            content=asset.description or "",
            author_id=asset.owner_id or "system",
            category_id=asset.asset_type.value,
            tags=asset.tags or [],
            view_count=asset.download_count * 10,
            like_count=0,
            comment_count=0,
            is_pinned=False,
            is_essence=False,
            created_at=asset.created_at,
            updated_at=asset.updated_at
        ))
    
    return posts


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取帖子详情"""
    result = await db.execute(select(Asset).where(Asset.id == post_id))
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    return PostResponse(
        id=asset.id,
        title=asset.name,
        content=asset.description or "",
        author_id=asset.owner_id or "system",
        category_id=asset.asset_type.value,
        tags=asset.tags or [],
        view_count=asset.download_count * 10,
        like_count=0,
        comment_count=0,
        is_pinned=False,
        is_essence=False,
        created_at=asset.created_at,
        updated_at=asset.updated_at
    )


@router.post("/posts", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建帖子"""
    # 创建为资产（简化实现）
    asset = Asset(
        name=post_data.title,
        description=post_data.content,
        asset_type="report",  # 帖子作为报告类型
        tags=post_data.tags,
        is_public=True,
        is_free=True,
        status="ready",
        owner_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    
    return PostResponse(
        id=asset.id,
        title=asset.name,
        content=asset.description or "",
        author_id=asset.owner_id,
        category_id=post_data.category_id,
        tags=post_data.tags or [],
        view_count=0,
        like_count=0,
        comment_count=0,
        is_pinned=False,
        is_essence=False,
        created_at=asset.created_at,
        updated_at=asset.updated_at
    )


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    post_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50)
):
    """获取评论列表"""
    return []


@router.get("/tags", response_model=List[TagResponse])
async def list_tags(
    limit: int = Query(20, ge=1, le=100)
):
    """获取热门标签"""
    return [
        {"id": "1", "name": "图像分类", "post_count": 150},
        {"id": "2", "name": "目标检测", "post_count": 120},
        {"id": "3", "name": "NLP", "post_count": 200},
        {"id": "4", "name": "语音识别", "post_count": 80},
        {"id": "5", "name": "大模型", "post_count": 300},
    ]