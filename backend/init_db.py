#!/usr/bin/env python3
"""初始化数据库和默认数据"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal, init_db
from app.core.security import get_password_hash
from app.models.user import User, Tenant, UserRole, UserStatus


async def create_default_tenant(db: AsyncSessionLocal):
    """创建默认租户"""
    tenant = Tenant(
        name="默认租户",
        description="系统默认租户",
        max_concurrent_tasks=10,
        max_storage_gb=100,
        max_users=50,
        balance=1000000,  # 10000元测试余额
        subscription_type="pro",
        status=UserStatus.ACTIVE,
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def create_admin_user(db: AsyncSessionLocal, tenant_id: str = None):
    """创建管理员用户"""
    admin = User(
        email="admin@aivalidation.cn",
        username="admin",
        hashed_password=get_password_hash("admin123"),
        full_name="系统管理员",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_superuser=True,
        tenant_id=tenant_id,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


async def create_test_user(db: AsyncSessionLocal, tenant_id: str):
    """创建测试用户"""
    user = User(
        email="user@example.com",
        username="testuser",
        hashed_password=get_password_hash("test123"),
        full_name="测试用户",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_active=True,
        tenant_id=tenant_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def main():
    """主函数"""
    print("初始化数据库...")
    
    # 创建表
    await init_db()
    print("✓ 数据库表创建完成")
    
    async with AsyncSessionLocal() as db:
        # 创建租户
        try:
            tenant = await create_default_tenant(db)
            print(f"✓ 默认租户创建完成: {tenant.name} (ID: {tenant.id})")
        except Exception as e:
            print(f"! 租户可能已存在: {e}")
            # 查询已存在的租户
            from sqlalchemy import select
            result = await db.execute(select(Tenant).limit(1))
            tenant = result.scalar_one_or_none()
            if tenant:
                print(f"  使用已有租户: {tenant.name}")
            else:
                raise
        
        # 创建管理员
        try:
            admin = await create_admin_user(db, tenant.id if tenant else None)
            print(f"✓ 管理员创建完成: {admin.username}")
            print(f"  密码: admin123")
        except Exception as e:
            print(f"! 管理员可能已存在: {e}")
        
        # 创建测试用户
        try:
            if tenant:
                test_user = await create_test_user(db, tenant.id)
                print(f"✓ 测试用户创建完成: {test_user.username}")
                print(f"  密码: test123")
        except Exception as e:
            print(f"! 测试用户可能已存在: {e}")
    
    print("\n初始化完成!")
    print("\n登录信息:")
    print("  管理员: admin / admin123")
    print("  测试用户: testuser / test123")


if __name__ == "__main__":
    asyncio.run(main())