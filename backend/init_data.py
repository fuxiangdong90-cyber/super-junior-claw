#!/usr/bin/env python3
"""初始化测试数据"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset, AssetType, AssetStatus
from app.models.user import User, Tenant
from sqlalchemy import select


async def create_sample_assets(db: AsyncSessionLocal):
    """创建示例资产"""
    # 获取租户
    result = await db.execute(select(Tenant).limit(1))
    tenant = result.scalar_one_or_none()
    
    # 获取用户
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    
    if not tenant or not user:
        print("! 需要先创建租户和用户")
        return
    
    assets_data = [
        {
            "name": "ImageNet-1K数据集",
            "description": "ImageNet分类数据集，包含1000个类别，128万张图片",
            "asset_type": AssetType.DATASET,
            "tags": ["图像分类", "benchmark", "1000类"],
            "is_public": True,
            "is_free": True,
            "status": AssetStatus.READY,
            "file_size": 150_000_000_000,  # ~150GB
        },
        {
            "name": "COCO-2017数据集",
            "description": "COCO目标检测数据集，包含80类，330K张图片",
            "asset_type": AssetType.DATASET,
            "tags": ["目标检测", "分割", "80类"],
            "is_public": True,
            "is_free": True,
            "status": AssetStatus.READY,
            "file_size": 25_000_000_000,  # ~25GB
        },
        {
            "name": "ResNet-50预训练模型",
            "description": "ResNet-50 ImageNet预训练模型",
            "asset_type": AssetType.MODEL,
            "tags": ["图像分类", "ResNet", "预训练"],
            "is_public": True,
            "is_free": True,
            "status": AssetStatus.READY,
            "file_size": 100_000_000,  # ~100MB
        },
        {
            "name": "BERT-Base中文模型",
            "description": "BERT-Base中文预训练模型，12层，768维",
            "asset_type": AssetType.MODEL,
            "tags": ["NLP", "BERT", "中文"],
            "is_public": True,
            "is_free": True,
            "status": AssetStatus.READY,
            "file_size": 400_000_000,  # ~400MB
        },
        {
            "name": "PyTorch 2.0框架",
            "description": "PyTorch深度学习框架",
            "asset_type": AssetType.FRAMEWORK,
            "tags": ["深度学习", "框架", "Python"],
            "is_public": True,
            "is_free": True,
            "status": AssetStatus.READY,
        },
        {
            "name": "OneFlow框架",
            "description": "国产深度学习框架OneFlow",
            "asset_type": AssetType.FRAMEWORK,
            "tags": ["国产", "深度学习", "框架"],
            "is_public": True,
            "is_free": True,
            "status": AssetStatus.READY,
        },
        {
            "name": "评测工具集",
            "description": "AI模型评测工具集，包含精度、性能、兼容性测试",
            "asset_type": AssetType.TOOL,
            "tags": ["评测", "工具", "性能测试"],
            "is_public": True,
            "is_free": True,
            "status": AssetStatus.READY,
        },
    ]
    
    for data in assets_data:
        asset = Asset(
            **data,
            owner_id=user.id,
            tenant_id=tenant.id,
        )
        db.add(asset)
    
    await db.commit()
    print(f"✓ 创建了 {len(assets_data)} 个示例资产")


async def create_sample_resources(db: AsyncSessionLocal):
    """创建示例算力资源"""
    from app.models.asset import ComputeResource
    
    resources_data = [
        {
            "name": "华为Ascend-910 节点1",
            "resource_type": "npu",
            "vendor": "华为",
            "model": "Ascend-910",
            "gpu_count": 8,
            "gpu_memory_gb": 256,
            "cpu_cores": 64,
            "cpu_memory_gb": 512,
            "storage_tb": 10,
            "source": "self",
            "status": "available",
            "price_per_hour": 400,  # 4元/小时
        },
        {
            "name": "华为Ascend-910 节点2",
            "resource_type": "npu",
            "vendor": "华为",
            "model": "Ascend-910",
            "gpu_count": 8,
            "gpu_memory_gb": 256,
            "cpu_cores": 64,
            "cpu_memory_gb": 512,
            "storage_tb": 10,
            "source": "self",
            "status": "available",
            "price_per_hour": 400,
        },
        {
            "name": "寒武纪MLU270节点",
            "resource_type": "npu",
            "vendor": "寒武纪",
            "model": "MLU270",
            "gpu_count": 4,
            "gpu_memory_gb": 128,
            "cpu_cores": 32,
            "cpu_memory_gb": 256,
            "storage_tb": 5,
            "source": "self",
            "status": "available",
            "price_per_hour": 300,
        },
        {
            "name": "摩尔线程MTT X400节点",
            "resource_type": "gpu",
            "vendor": "摩尔线程",
            "model": "MTT X400",
            "gpu_count": 4,
            "gpu_memory_gb": 128,
            "cpu_cores": 32,
            "cpu_memory_gb": 256,
            "storage_tb": 5,
            "source": "self",
            "status": "available",
            "price_per_hour": 250,
        },
        {
            "name": "NVIDIA A100云服务器",
            "resource_type": "gpu",
            "vendor": "NVIDIA",
            "model": "A100",
            "gpu_count": 1,
            "gpu_memory_gb": 40,
            "cpu_cores": 8,
            "cpu_memory_gb": 64,
            "storage_tb": 1,
            "source": "cloud",
            "cloud_provider": "阿里云",
            "cloud_region": "华东1",
            "status": "available",
            "price_per_hour": 800,
        },
    ]
    
    for data in resources_data:
        resource = ComputeResource(**data)
        db.add(resource)
    
    await db.commit()
    print(f"✓ 创建了 {len(resources_data)} 个示例算力资源")


async def main():
    async with AsyncSessionLocal() as db:
        await create_sample_assets(db)
        await create_sample_resources(db)
        print("\n✓ 示例数据创建完成!")


if __name__ == "__main__":
    asyncio.run(main())