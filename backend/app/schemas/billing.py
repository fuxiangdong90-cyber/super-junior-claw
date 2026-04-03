"""计费Schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BalanceResponse(BaseModel):
    """余额响应"""
    balance: int  # 余额（分）
    tenant_id: Optional[str] = None
    subscription_type: str = "free"
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """订单响应"""
    id: str
    order_no: str
    tenant_id: str
    amount: int  # 金额（分）
    status: str  # pending, paid, cancelled, refunded
    order_type: str  # recharge, evaluation, storage
    description: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """创建订单"""
    order_type: str
    amount: int
    description: Optional[str] = None


class RechargeRequest(BaseModel):
    """充值请求"""
    amount: float = Field(..., gt=0, description="充值金额（元）")
    payment_method: str = "alipay"  # alipay, wechat, bank
    promo_code: Optional[str] = None


class RechargeResponse(BaseModel):
    """充值响应"""
    success: bool
    amount: float
    new_balance: int
    transaction_id: str
    message: Optional[str] = None


class InvoiceResponse(BaseModel):
    """发票响应"""
    id: str
    invoice_no: str
    tenant_id: str
    order_id: Optional[str] = None
    amount: int  # 金额（分）
    tax_amount: int  # 税额（分）
    title: str  # 发票抬头
    tax_number: str  # 税号
    status: str  # pending, issued, rejected
    created_at: datetime
    issued_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CostEstimateResponse(BaseModel):
    """费用预估响应"""
    task_id: str
    estimated_hours: float
    gpu_count: int
    gpu_model: Optional[str]
    unit_price: int  # 每小时价格（分）
    total_cost: int  # 总费用（分）
    breakdown: dict