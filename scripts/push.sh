#!/bin/bash
# 一键推送脚本 - 本地执行

set -e

REPO_URL="https://github.com/fuxiangdong90-cyber/super-junior-claw.git"
SOURCE_DIR="ai-validation-platform"

echo "=========================================="
echo "  一键推送 AI Validation Platform"
echo "=========================================="

# 检查是否有tar.gz文件
if [ -f "$SOURCE_DIR.tar.gz" ]; then
    echo "使用现有的tar.gz文件..."
    tar -xzvf $SOURCE_DIR.tar.gz
elif [ -d "$SOURCE_DIR" ]; else
    echo "请确保 $SOURCE_DIR 目录或 $SOURCE_DIR.tar.gz 存在"
    exit 1
fi

cd $SOURCE_DIR

# 初始化git（如果需要）
if [ ! -d .git ]; then
    echo "初始化Git仓库..."
    git init
    git branch -M main
fi

# 设置远程仓库
echo "设置远程仓库..."
git remote remove origin 2>/dev/null || true
git remote add origin $REPO_URL

# 添加所有文件
echo "添加文件..."
git add -A

# 提交
echo "提交代码..."
git commit -m "feat: AI软硬件验证平台 - 完整实现

后端 (FastAPI):
- 用户认证 (JWT)
- 评测任务管理
- 资产管理
- 算力资源管理
- 计费系统
- 社区服务
- Celery任务调度
- PostgreSQL + Redis + RabbitMQ

前端 (React + TypeScript):
- 登录/仪表盘
- 任务管理
- 资产管理
- 资源管理
- 社区页面

部署:
- Docker Compose
- Kubernetes K8s
- Helm Chart
- CI/CD GitHub Actions

文档:
- 架构设计
- 快速开始" 2>/dev/null || echo "Nothing to commit"

# 推送
echo "推送到GitHub..."
echo "请输入GitHub Token或使用SSH"
read -p "是否使用SSH推送? (y/n): " USE_SSH

if [ "$USE_SSH" = "y" ]; then
    git remote set-url origin git@github.com:fuxiangdong90-cyber/super-junior-claw.git
fi

git push -u origin main

echo ""
echo "=========================================="
echo "  ✅ 推送完成!"
echo "=========================================="