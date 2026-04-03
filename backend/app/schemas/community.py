"""社区Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryResponse(BaseModel):
    """分类响应"""
    id: str
    name: str
    description: str
    post_count: int
    
    class Config:
        from_attributes = True


class TagResponse(BaseModel):
    """标签响应"""
    id: str
    name: str
    post_count: int
    
    class Config:
        from_attributes = True


class PostBase(BaseModel):
    """帖子基础"""
    title: str = Field(..., min_length=5, max_length=200)
    content: str = Field(..., min_length=10)
    category_id: str
    tags: Optional[List[str]] = None


class PostCreate(PostBase):
    """创建帖子"""
    is_anonymous: bool = False


class PostUpdate(BaseModel):
    """更新帖子"""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class PostResponse(BaseModel):
    """帖子响应"""
    id: str
    title: str
    content: str
    author_id: str
    category_id: str
    tags: List[str] = []
    view_count: int
    like_count: int
    comment_count: int
    is_pinned: bool
    is_essence: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    """评论基础"""
    content: str = Field(..., min_length=1, max_length=2000)


class CommentCreate(CommentBase):
    """创建评论"""
    post_id: str
    parent_id: Optional[str] = None


class CommentResponse(BaseModel):
    """评论响应"""
    id: str
    post_id: str
    author_id: str
    content: str
    parent_id: Optional[str] = None
    like_count: int
    reply_count: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LikeRequest(BaseModel):
    """点赞请求"""
    target_type: str  # post, comment
    target_id: str


class LikeResponse(BaseModel):
    """点赞响应"""
    success: bool
    like_count: int