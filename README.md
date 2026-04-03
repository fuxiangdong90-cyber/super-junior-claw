# AI Validation Platform - 技术总结

## 项目概述

国产AI软硬件全栈式验证平台 - 覆盖芯片、算子、中间层、框架、模型、场景的全链路评测。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10 + FastAPI + SQLAlchemy 2.0 |
| 前端 | React 18 + TypeScript + Ant Design 5 |
| 数据库 | PostgreSQL 15 |
| 缓存 | Redis 7 |
| 消息队列 | RabbitMQ |
| 任务调度 | Celery |
| 部署 | Kubernetes + Helm |
| 监控 | Prometheus + Grafana |
| CI/CD | GitHub Actions |

## 核心功能模块

### 1. 用户与租户管理
- [x] JWT认证
- [x] 多租户隔离
- [x] 角色权限 (RBAC)

### 2. 评测任务系统
- [x] 任务创建/编辑/删除
- [x] 任务调度 (Celery)
- [x] 优先级队列
- [x] 任务状态管理
- [x] 任务日志

### 3. 资产管理
- [x] 数据集管理
- [x] 模型管理
- [x] 框架管理
- [x] 工具管理
- [x] 镜像管理
- [x] 公开/免费资源

### 4. 算力资源管理
- [x] 资源注册
- [x] 资源调度
- [x] 资源监控
- [x] 异构资源 (GPU/NPU/FPGA)
- [x] 云厂商资源接入

### 5. 计费系统
- [x] 余额管理
- [x] 充值
- [x] 订单管理
- [x] 价格表
- [x] 发票管理

### 6. 社区
- [x] 帖子列表
- [x] 分类浏览
- [x] 标签管理
- [x] 资源下载

### 7. 监控运维
- [x] Prometheus指标
- [x] 告警规则
- [x] 健康检查
- [x] 日志收集

## API接口

### 认证
- `POST /api/v1/auth/register` - 注册
- `POST /api/v1/auth/login` - 登录
- `GET /api/v1/auth/me` - 当前用户

### 评测任务
- `GET /api/v1/tasks` - 任务列表
- `POST /api/v1/tasks` - 创建任务
- `GET /api/v1/tasks/{id}` - 任务详情
- `PATCH /api/v1/tasks/{id}` - 更新任务
- `DELETE /api/v1/tasks/{id}` - 删除任务
- `GET /api/v1/tasks/{id}/logs` - 任务日志

### 资产
- `GET /api/v1/assets` - 资产列表
- `POST /api/v1/assets` - 创建资产
- `GET /api/v1/assets/{id}` - 资产详情

### 资源
- `GET /api/v1/resources` - 资源列表
- `POST /api/v1/resources` - 添加资源

### 计费
- `GET /api/v1/billing/balance` - 余额
- `POST /api/v1/billing/recharge` - 充值
- `GET /api/v1/billing/prices` - 价格表

### 社区
- `GET /api/v1/community/posts` - 帖子列表
- `GET /api/v1/community/categories` - 分类
- `GET /api/v1/community/tags` - 标签

## 部署方式

### Docker Compose (开发)
```bash
docker-compose up -d
```

### Kubernetes (生产)
```bash
kubectl apply -k k8s/overlays/prod/
```

### Helm
```bash
helm install ai-validation ./helm -n ai-validation --create-namespace
```

## 项目结构

```
ai-validation-platform/
├── backend/              # FastAPI后端
│   ├── app/
│   │   ├── api/         # API路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据库模型
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # 业务逻辑
│   └── tests/           # 测试
├── frontend/            # React前端
│   └── src/
│       ├── pages/       # 页面组件
│       ├── components/  # 公共组件
│       ├── hooks/       # 自定义hooks
│       └── services/    # API服务
├── k8s/                 # Kubernetes配置
├── helm/                # Helm Chart
├── scripts/             # 部署脚本
└── docs/                # 文档
```

## 快速开始

详见 [QUICKSTART.md](./docs/QUICKSTART.md)

## 许可

MIT License