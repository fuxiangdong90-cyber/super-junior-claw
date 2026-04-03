"""系统状态API"""
import time
from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any
import psutil

router = APIRouter(tags=["系统"])

# 启动时间
START_TIME = time.time()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ai-validation-platform",
        "version": "1.0.0"
    }


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """就绪检查"""
    # 可以在这里添加数据库、Redis等依赖检查
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """存活检查"""
    uptime = time.time() - START_TIME
    return {
        "status": "alive",
        "uptime_seconds": int(uptime),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """系统状态"""
    # CPU和内存信息
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    uptime = time.time() - START_TIME
    
    return {
        "service": "ai-validation-platform",
        "version": "1.0.0",
        "environment": "production",
        "uptime_seconds": int(uptime),
        "system": {
            "cpu": {
                "usage_percent": cpu_percent,
                "count": psutil.cpu_count(),
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "usage_percent": disk.percent,
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """Prometheus格式指标"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    # 返回Prometheus格式的文本
    metrics_text = f"""# HELP python_cpu_usage Python CPU usage
# TYPE python_cpu_usage gauge
python_cpu_usage {cpu_percent}

# HELP python_memory_usage Python memory usage in bytes
# TYPE python_memory_usage gauge
python_memory_usage {memory.used}

# HELP python_memory_percent Memory usage percentage
# TYPE python_memory_percent gauge
python_memory_percent {memory.percent}

# HELP ai_validation_uptime_seconds Service uptime in seconds
# TYPE ai_validation_uptime_seconds gauge
ai_validation_uptime_seconds {time.time() - START_TIME}
"""
    
    return {"metrics": metrics_text}