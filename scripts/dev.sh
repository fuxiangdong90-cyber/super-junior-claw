#!/bin/bash
# 本地开发启动脚本

set -e

echo "启动AI Validation Platform本地开发环境..."

# 启动基础设施服务
echo "启动数据库、Redis、消息队列..."
docker-compose up -d postgres redis rabbitmq

# 等待数据库就绪
echo "等待数据库就绪..."
sleep 5

# 启动后端
echo "启动后端服务..."
cd backend
pip install -r requirements.txt -q
uvicorn main:app --reload --host 0.0.0.0 &

# 启动前端
echo "启动前端服务..."
cd ../frontend
npm install -q
npm run dev &

echo ""
echo "✅ 服务启动完成!"
echo "  - 后端: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo "  - 前端: http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止所有服务"