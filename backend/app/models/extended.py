"""通知系统模型"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
    """通知类型"""
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_QUEUED = "task_queued"
    REPORT_READY = "report_ready"
    BALANCE_LOW = "balance_low"
    SYSTEM公告 = "system_公告"
    USER_INVITE = "user_invite"


class NotificationLevel(str, enum.Enum):
    """通知级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class Notification(Base):
    """通知表"""
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 通知内容
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    level = Column(SQLEnum(NotificationLevel), default=NotificationLevel.INFO)
    
    # 关联数据
    related_id = Column(String(36))  # 关联的任务/报告等ID
    related_type = Column(String(50))  # task, report, asset等
    
    # 链接
    action_url = Column(String(255))  # 点击跳转链接
    
    # 状态
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    # 发送方式
    email_sent = Column(Boolean, default=False)
    sms_sent = Column(Boolean, default=False)
    
    # 接收者
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", backref="notifications")
    
    def __repr__(self):
        return f"<Notification {self.title}>"


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    value_type = Column(String(20), default="string")  # string, int, float, bool, json
    
    # 配置描述
    description = Column(String(255))
    category = Column(String(50))  # system, feature, billing, integration
    
    # 状态
    is_public = Column(Boolean, default=False)  # 是否公开
    is_editable = Column(Boolean, default=True)  # 是否可编辑
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(36), ForeignKey("users.id"))
    
    def __repr__(self):
        return f"<SystemConfig {self.key}>"


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 操作信息
    action = Column(String(100), nullable=False)  # create, update, delete, login, logout
    resource = Column(String(50), nullable=False)  # user, task, asset, report等
    resource_id = Column(String(36))
    
    # 请求信息
    method = Column(String(10))  # GET, POST, PUT, DELETE
    path = Column(String(255))
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    # 请求参数
    request_body = Column(JSON)
    response_status = Column(Integer)
    
    # 操作用户
    user_id = Column(String(36), ForeignKey("users.id"))
    tenant_id = Column(String(36))
    
    # 结果
    result = Column(String(20))  # success, failure
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource}>"


class APIKey(Base):
    """API密钥表"""
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 密钥信息
    name = Column(String(100), nullable=False)
    key = Column(String(64), unique=True, nullable=False)
    secret = Column(String(128))  # 加密存储
    
    # 权限
    permissions = Column(JSON, default=list)  # ["task:read", "task:write"]
    
    # 限制
    rate_limit = Column(Integer, default=100)  # 每分钟请求数
    daily_limit = Column(Integer, default=10000)  # 每日请求数
    
    # 使用统计
    request_count = Column(Integer, default=0)
    last_request_at = Column(DateTime)
    
    # 状态
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    
    # 所有者
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String(36))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<APIKey {self.name}>"


class Webhook(Base):
    """Webhook配置表"""
    __tablename__ = "webhooks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 配置
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    method = Column(String(10), default="POST")  # POST, PUT
    headers = Column(JSON)  # 自定义请求头
    
    # 触发事件
    events = Column(JSON, default=list)  # ["task.completed", "task.failed"]
    
    # 状态
    is_active = Column(Boolean, default=True)
    secret = Column(String(64))  # 用于签名
    
    # 统计
    total_calls = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    last_called_at = Column(DateTime)
    last_status_code = Column(Integer)
    
    # 所有者
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String(36))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Webhook {self.name}>"


class Invitation(Base):
    """邀请表"""
    __tablename__ = "invitations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 邀请信息
    email = Column(String(255), nullable=False)
    role = Column(String(50), default="member")
    
    # 邀请码
    code = Column(String(32), unique=True, nullable=False)
    expires_at = Column(DateTime)
    
    # 状态
    status = Column(String(20), default="pending")  # pending, accepted, expired
    
    # 邀请人
    invited_by = Column(String(36), ForeignKey("users.id"))
    tenant_id = Column(String(36), ForeignKey("tenants.id"))
    
    # 被邀请人
    user_id = Column(String(36), ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Invitation {self.email}>"