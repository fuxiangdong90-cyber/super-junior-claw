"""用户模型"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """用户角色"""
    ADMIN = "admin"
    TENANT_ADMIN = "tenant_admin"
    USER = "user"
    GUEST = "guest"


class UserStatus(str, enum.Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    BANNED = "banned"


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 租户信息
    tenant_id = Column(String(36), index=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # 关系
    tenant = relationship("Tenant", back_populates="users", foreign_keys=[tenant_id])
    evaluation_tasks = relationship("EvaluationTask", back_populates="user")
    assets = relationship("Asset", back_populates="owner")
    
    def __repr__(self):
        return f"<User {self.username}>"


class Tenant(Base):
    """租户表"""
    __tablename__ = "tenants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
    
    # 资源限制
    max_concurrent_tasks = Column(Integer, default=5)
    max_storage_gb = Column(Integer, default=100)
    max_users = Column(Integer, default=10)
    
    # 配额使用
    used_concurrent_tasks = Column(Integer, default=0)
    used_storage_gb = Column(Integer, default=0)
    
    # 计费
    balance = Column(Integer, default=0)  # 余额（分）
    subscription_type = Column(String(50), default="free")  # free, basic, pro
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    users = relationship("User", back_populates="tenant", foreign_keys="User.tenant_id")
    evaluation_tasks = relationship("EvaluationTask", back_populates="tenant")
    assets = relationship("Asset", back_populates="tenant")
    
    def __repr__(self):
        return f"<Tenant {self.name}>"