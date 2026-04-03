#!/bin/bash
# 部署脚本 - 一键部署到K8s

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  AI Validation Platform 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 环境检查
echo -e "${YELLOW}[1/6] 检查环境...${NC}"
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl 未安装${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker 未安装${NC}"
    exit 1
fi

# 选择环境
echo -e "${YELLOW}[2/6] 选择部署环境:${NC}"
echo "1) 开发环境 (dev)"
echo "2) 生产环境 (prod)"
read -p "请输入选项 [1]: " ENV_CHOICE
ENV_CHOICE=${ENV_CHOICE:-1}

if [ "$ENV_CHOICE" = "1" ]; then
    ENV="dev"
elif [ "$ENV_CHOICE" = "2" ]; then
    ENV="prod"
else
    ENV="dev"
fi

echo -e "部署到: ${GREEN}$ENV${NC}"

# 构建镜像
echo -e "${YELLOW}[3/6] 构建Docker镜像...${NC}"
REGISTRY=${REGISTRY:-"docker.io"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}

echo "构建后端镜像..."
docker build -t ai-validation-backend:$IMAGE_TAG ./backend

echo "构建前端镜像..."
docker build -t ai-validation-frontend:$IMAGE_TAG ./frontend

# 推送到仓库 (可选)
if [ "$PUSH_IMAGE" = "true" ]; then
    echo -e "${YELLOW}推送镜像到仓库...${NC}"
    docker tag ai-validation-backend:$IMAGE_TAG $REGISTRY/ai-validation-backend:$IMAGE_TAG
    docker tag ai-validation-frontend:$IMAGE_TAG $REGISTRY/ai-validation-frontend:$IMAGE_TAG
    docker push $REGISTRY/ai-validation-backend:$IMAGE_TAG
    docker push $REGISTRY/ai-validation-frontend:$IMAGE_TAG
fi

# 部署到K8s
echo -e "${YELLOW}[4/6] 部署到Kubernetes...${NC}"

# 应用基础配置
kubectl apply -k k8s/base/

# 应用环境配置
kubectl apply -k k8s/overlays/$ENV/

# 等待部署
echo -e "${YELLOW}[5/6] 等待服务启动...${NC}"
kubectl wait --for=condition=available deployment/backend -n ai-validation --timeout=300s
kubectl wait --for=condition=available deployment/frontend -n ai-validation --timeout=300s

# 检查状态
echo -e "${YELLOW}[6/6] 检查服务状态...${NC}"
kubectl get pods -n ai-validation
kubectl get svc -n ai-validation

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "访问地址:"
echo "  - 前端: http://localhost:3000"
echo "  - 后端: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo ""
echo "查看日志:"
echo "  kubectl logs -n ai-validation -l app=backend"
echo "  kubectl logs -n ai-validation -l app=frontend"