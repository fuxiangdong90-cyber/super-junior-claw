"""计费服务API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User, Tenant
from app.schemas.billing import (
    BalanceResponse, OrderCreate, OrderResponse,
    RechargeRequest, RechargeResponse, InvoiceResponse
)

router = APIRouter(prefix="/billing", tags=["计费"])


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取账户余额"""
    if current_user.tenant_id:
        result = await db.execute(
            select(Tenant).where(Tenant.id == current_user.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if tenant:
            return BalanceResponse(
                balance=tenant.balance,
                tenant_id=tenant.id,
                subscription_type=tenant.subscription_type
            )
    
    return BalanceResponse(balance=0, subscription_type="free")


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取订单列表"""
    # 简化实现，返回空列表
    return []


@router.post("/recharge", response_model=RechargeResponse)
async def recharge(
    recharge_data: RechargeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """充值"""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant associated with user"
        )
    
    # 更新租户余额
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # 添加充值金额（实际需要对接支付网关）
    amount_cents = recharge_data.amount * 100  # 转换为分
    tenant.balance += int(amount_cents)
    
    await db.commit()
    
    return RechargeResponse(
        success=True,
        amount=recharge_data.amount,
        new_balance=tenant.balance,
        transaction_id=f"tx_{datetime.utcnow().timestamp()}"
    )


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取发票列表"""
    return []


@router.get("/prices")
async def get_prices():
    """获取价格表"""
    return {
        "evaluation_types": {
            "performance": {"name": "性能评测", "base_price": 100, "unit": "元/小时/GPU"},
            "precision": {"name": "精度评测", "base_price": 80, "unit": "元/小时/GPU"},
            "compatibility": {"name": "兼容性评测", "base_price": 120, "unit": "元/小时/GPU"},
            "stability": {"name": "稳定性评测", "base_price": 150, "unit": "元/小时/GPU"}
        },
        "resources": {
            "Ascend-910": {"price": 50, "unit": "元/小时"},
            "Kunlun-910": {"price": 45, "unit": "元/小时"},
            "NVIDIA-A100": {"price": 80, "unit": "元/小时"},
            "NVIDIA-H100": {"price": 120, "unit": "元/小时"}
        },
        "storage": {"price": 0.5, "unit": "元/GB/月"},
        "bandwidth": {"price": 0.8, "unit": "元/GB"}
    }