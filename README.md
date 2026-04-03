# 人工智能软硬件验证平台 (AI Validation Platform)

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-red.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)

国产AI软硬件全栈式验证平台 - 覆盖芯片、算子、中间层、框架、模型、场景的全链路评测。

## 核心功能

- ✅ 全栈自动化评测（芯片→模型→场景）
- ✅ 多租户隔离
- ✅ 异构资源纳管
- ✅ 评测任务管理（创建、调度、执行、监控）
- ✅ 评测结果与资产管理
- ✅ 验证平台社区
- ✅ 用户体系与权限管理
- ✅ 市场化计费系统

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy |
| 前端 | React 18 + TypeScript + Vite |
| 数据库 | PostgreSQL 15+ |
| 缓存 | Redis |
| 任务队列 | Celery + RabbitMQ |
| 部署 | Kubernetes (K8s) |
| CI/CD | GitHub Actions |

## 快速开始

### 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/your-repo/ai-validation-platform.git
cd ai-validation-platform

# 2. 启动后端
cd backend
cp .env.example .env
# 编辑 .env 配置数据库等
docker-compose up -d

# 3. 启动前端
cd ../frontend
npm install
npm run dev
```

### K8s 部署

```bash
cd k8s/overlays/dev
kubectl apply -k .
```

## 项目结构

```
ai-validation-platform/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据库模型
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # 业务逻辑
│   ├── tests/           # 测试
│   └── main.py          # 入口
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── components/  # 组件
│   │   ├── pages/       # 页面
│   │   ├── hooks/       # Hooks
│   │   ├── services/    # API服务
│   │   └── types/       # 类型定义
│   └── public/
├── k8s/                 # K8s配置
│   ├── base/           # 基础配置
│   └── overlays/       # 环境覆盖
└── docs/               # 文档
```

## API 文档

启动后端服务后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 许可证

MIT License - 查看 [LICENSE](LICENSE) 了解更多