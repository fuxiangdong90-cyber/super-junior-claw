# 快速开始

## 本地开发

### 前置要求

- Docker & Docker Compose
- Python 3.10+
- Node.js 18+
- Git

### 1. 克隆项目

```bash
git clone https://github.com/fuxiangdong90-cyber/super-junior-claw.git
cd super-junior-claw
```

### 2. 启动基础设施

```bash
# 启动数据库、Redis、消息队列
docker-compose up -d postgres redis rabbitmq
```

### 3. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 复制配置
cp .env.example .env
# 编辑 .env 配置数据库密码等

# 启动服务
uvicorn main:app --reload
```

后端运行在: http://localhost:8000
API文档: http://localhost:8000/docs

### 4. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在: http://localhost:3000

### 5. 访问系统

打开浏览器访问 http://localhost:3000

默认管理员账号:
- 用户名: admin
- 密码: admin123

## 一键启动 (Linux/Mac)

```bash
bash scripts/dev.sh
```

## 生产部署

### Docker Compose

```bash
docker-compose up -d
```

### Kubernetes

```bash
# 方式1: 使用Kustomize
kubectl apply -k k8s/overlays/prod/

# 方式2: 使用Helm
helm install ai-validation ./helm -f ./helm/values.yaml -n ai-validation --create-namespace

# 方式3: 使用部署脚本
bash scripts/deploy.sh
```

## 环境变量

### 后端 (.env)

```env
# App
APP_NAME=AI Validation Platform
DEBUG=true

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=ai_validation

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# RabbitMQ
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
```

### 前端 (.env)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 目录结构

```
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据库模型
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # 业务服务
│   ├── tests/           # 测试
│   └── main.py          # 入口
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── pages/       # 页面
│   │   ├── components/  # 组件
│   │   ├── hooks/       # Hooks
│   │   └── services/    # API服务
│   └── public/
├── k8s/                 # K8s配置
├── helm/                # Helm Chart
├── scripts/             # 脚本
└── docs/                # 文档
```

## 常见问题

### 1. 数据库连接失败

检查PostgreSQL是否运行:
```bash
docker ps | grep postgres
```

### 2. 前端无法连接后端

检查后端是否运行:
```bash
curl http://localhost:8000/health
```

### 3. 端口被占用

修改 docker-compose.yml 中的端口映射

## 下一步

- [架构设计](./docs/ARCHITECTURE.md)
- [API文档](http://localhost:8000/docs)
- [部署指南](./docs/DEPLOYMENT.md)