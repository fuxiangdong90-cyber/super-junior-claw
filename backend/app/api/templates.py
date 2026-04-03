"""评测模板API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.task import EvaluationType, EvaluationTarget

router = APIRouter(prefix="/templates", tags=["评测模板"])

# 预定义模板
TEMPLATES = [
    # 芯片性能评测
    {
        "id": "chip-perf-basic",
        "name": "芯片基础性能评测",
        "description": "评估芯片基本计算性能，包括算力、内存带宽等",
        "evaluation_type": "performance",
        "evaluation_target": "chip",
        "category": "芯片",
        "default_config": {
            "test_suite": "basic",
            "warmup_iterations": 100,
            "test_iterations": 1000,
            "batch_sizes": [1, 8, 16, 32, 64],
        },
        "is_free": True,
        "estimated_time_hours": 2,
    },
    {
        "id": "chip-perf-advanced",
        "name": "芯片深度性能评测",
        "description": "全面的芯片性能评测，包含多种模型推理测试",
        "evaluation_type": "performance",
        "evaluation_target": "chip",
        "category": "芯片",
        "default_config": {
            "test_suite": "advanced",
            "models": ["resnet50", "vgg16", "bert-base"],
            "precision": ["fp32", "fp16", "int8"],
        },
        "is_free": False,
        "estimated_time_hours": 8,
    },
    # 算子兼容性评测
    {
        "id": "operator-compat",
        "name": "算子兼容性评测",
        "description": "测试算子在芯片上的兼容性",
        "evaluation_type": "compatibility",
        "evaluation_target": "operator",
        "category": "算子",
        "default_config": {
            "operator_list": "standard",
            "test_precision": ["fp32", "fp16"],
        },
        "is_free": True,
        "estimated_time_hours": 4,
    },
    # 框架适配评测
    {
        "id": "framework-adaptation",
        "name": "框架适配评测",
        "description": "评估深度学习框架在芯片上的适配情况",
        "evaluation_type": "compatibility",
        "evaluation_target": "framework",
        "category": "框架",
        "default_config": {
            "frameworks": ["pytorch", "tensorflow", "oneflow"],
            "test_models": 10,
        },
        "is_free": True,
        "estimated_time_hours": 6,
    },
    # 模型精度评测
    {
        "id": "model-accuracy",
        "name": "模型精度评测",
        "description": "评估模型在芯片上的精度表现",
        "evaluation_type": "precision",
        "evaluation_target": "model",
        "category": "模型",
        "default_config": {
            "datasets": ["imagenet", "coco"],
            "metrics": ["accuracy", "precision", "recall", "f1"],
        },
        "is_free": True,
        "estimated_time_hours": 3,
    },
    # 稳定性评测
    {
        "id": "stability-24h",
        "name": "24小时稳定性测试",
        "description": "长时间运行稳定性测试",
        "evaluation_type": "stability",
        "evaluation_target": "chip",
        "category": "稳定性",
        "default_config": {
            "duration_hours": 24,
            "load_pattern": "stress",
            "monitor_metrics": ["memory", "temperature", "error_rate"],
        },
        "is_free": False,
        "estimated_time_hours": 25,
    },
    # 场景评测
    {
        "id": "scenario-cv",
        "name": "计算机视觉场景评测",
        "description": "CV场景综合评测",
        "evaluation_type": "performance",
        "evaluation_target": "scenario",
        "category": "场景",
        "default_config": {
            "scenarios": ["classification", "detection", "segmentation"],
            "models": ["resnet", "yolo", "unet"],
        },
        "is_free": True,
        "estimated_time_hours": 5,
    },
    {
        "id": "scenario-nlp",
        "name": "NLP场景评测",
        "description": "自然语言处理场景综合评测",
        "evaluation_type": "performance",
        "evaluation_target": "scenario",
        "category": "场景",
        "default_config": {
            "scenarios": ["text_classification", "ner", "translation"],
            "models": ["bert", "gpt", "llama"],
        },
        "is_free": True,
        "estimated_time_hours": 6,
    },
]


@router.get("")
async def list_templates(
    category: Optional[str] = None,
    evaluation_type: Optional[str] = None,
    is_free: Optional[bool] = None,
):
    """获取评测模板列表"""
    result = TEMPLATES
    
    if category:
        result = [t for t in result if t.get("category") == category]
    if evaluation_type:
        result = [t for t in result if t["evaluation_type"] == evaluation_type]
    if is_free is not None:
        result = [t for t in result if t["is_free"] == is_free]
    
    return result


@router.get("/categories")
async def list_categories():
    """获取模板分类"""
    categories = {}
    for template in TEMPLATES:
        cat = template.get("category", "其他")
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    
    return [
        {"id": cat, "name": cat, "count": count}
        for cat, count in categories.items()
    ]


@router.get("/{template_id}")
async def get_template(template_id: str):
    """获取模板详情"""
    for template in TEMPLATES:
        if template["id"] == template_id:
            return template
    
    return {"error": "Template not found", "status": 404}