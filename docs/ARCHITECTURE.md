# 人工智能软硬件验证平台 - 架构设计文档

## 1. 系统架构

### 1.1 整体架构

本平台采用微服务架构，分为以下层次：

- **用户层**: Web前端、移动端H5、社区门户
- **API网关层**: 认证、限流、路由
- **服务层**: 核心业务服务
- **基础设施层**: 数据库、缓存、消息队列
- **算力资源层**: 异构算力统一管理

### 1.2 技术栈

| 组件 | 技术选型 | 版本 |
|------|----------|------|
| 后端框架 | FastAPI | 0.109+ |
| 数据库 | PostgreSQL | 15+ |
| 缓存 | Redis | 7+ |
| 消息队列 | RabbitMQ | 3.12+ |
| 任务调度 | Celery | 5.3+ |
| 前端 | React | 18+ |
| UI框架 | Ant Design | 5.12+ |
| 部署 | Kubernetes | 1.28+ |
| 监控 | Prometheus | 2.45+ |

## 2. 微服务设计

### 2.1 服务列表

| 服务名 | 职责 | 端口 |
|--------|------|------|
| user-srv | 用户、租户、权限管理 | 8001 |
| task-srv | 评测任务生命周期管理 | 8002 |
| asset-srv | 资产、数据集、镜像管理 | 8003 |
| resource-srv | 算力资源管理 | 8004 |
| billing-srv | 计费、订单、结算 | 8005 |
| portal-srv | 社区门户、论坛 | 8006 |
| scheduler-srv | 任务调度、资源分配 | 8007 |
| api-gateway | 统一入口、认证、限流 | 8000 |

### 2.2 服务通信

- **同步通信**: HTTP/gRPC (服务间调用)
- **异步通信**: RabbitMQ (事件驱动)

## 3. 数据库设计

### 3.1 核心实体

#### User (用户)
```python
- id: UUID (PK)
- email: string (unique)
- username: string (unique)
- hashed_password: string
- full_name: string
- role: enum (admin/tenant_admin/user/guest)
- status: enum (active/inactive/pending/banned)
- tenant_id: UUID (FK)
- is_superuser: boolean
- created_at: datetime
- updated_at: datetime
- last_login: datetime
```

#### Tenant (租户)
```python
- id: UUID (PK)
- name: string
- description: text
- max_concurrent_tasks: integer
- max_storage_gb: integer
- max_users: integer
- balance: integer (余额，分)
- subscription_type: string (free/basic/professional)
- created_at: datetime
```

#### EvaluationTask (评测任务)
```python
- id: UUID (PK)
- name: string
- evaluation_type: enum (performance/precision/compatibility/stability)
- evaluation_target: enum (chip/operator/framework/model/scenario)
- status: enum (pending/queued/running/completed/failed/cancelled)
- priority: enum (low/medium/high/urgent)
- progress: float (0-100)
- config: json
- result: json
- required_gpu_count: integer
- required_gpu_model: string
- user_id: UUID (FK)
- tenant_id: UUID (FK)
- created_at: datetime
- started_at: datetime
- finished_at: datetime
```

#### Asset (资产)
```python
- id: UUID (PK)
- name: string
- asset_type: enum (dataset/model/framework/tool/report/image)
- status: enum (uploading/ready/processing/failed)
- file_path: string
- file_size: bigint
- checksum: string (SHA256)
- is_public: boolean
- is_free: boolean
- download_count: integer
- owner_id: UUID (FK)
- tenant_id: UUID (FK)
- created_at: datetime
```

#### ComputeResource (算力资源)
```python
- id: UUID (PK)
- name: string
- resource_type: string (gpu/cpu/npu/fpga)
- vendor: string (华为/寒武纪/摩尔线程)
- model: string (Ascend-910/Kunlun-910)
- gpu_count: integer
- gpu_memory_gb: integer
- cpu_cores: integer
- cpu_memory_gb: integer
- source: enum (self/cloud/user)
- status: enum (available/busy/offline/maintenance)
- price_per_hour: integer (分)
- created_at: datetime
```

## 4. API设计

### 4.1 用户认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/register | 用户注册 |
| POST | /api/v1/auth/login | 用户登录 |
| GET | /api/v1/auth/me | 获取当前用户 |
| POST | /api/v1/auth/refresh | 刷新Token |

### 4.2 评测任务

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/tasks | 任务列表 |
| POST | /api/v1/tasks | 创建任务 |
| GET | /api/v1/tasks/{id} | 任务详情 |
| PATCH | /api/v1/tasks/{id} | 更新任务 |
| DELETE | /api/v1/tasks/{id} | 删除任务 |
| GET | /api/v1/tasks/{id}/logs | 任务日志 |
| GET | /api/v1/tasks/{id}/result | 评测结果 |

### 4.3 资产管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/assets | 资产列表 |
| POST | /api/v1/assets | 创建资产 |
| GET | /api/v1/assets/{id} | 资产详情 |
| PATCH | /api/v1/assets/{id} | 更新资产 |
| DELETE | /api/v1/assets/{id} | 删除资产 |
| GET | /api/v1/assets/{id}/download | 下载资产 |

### 4.4 算力资源

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/resources | 资源列表 |
| POST | /api/v1/resources | 添加资源 |
| GET | /api/v1/resources/{id} | 资源详情 |
| PATCH | /api/v1/resources/{id} | 更新资源 |
| DELETE | /api/v1/resources/{id} | 删除资源 |

### 4.5 计费

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/billing/balance | 账户余额 |
| GET | /api/v1/billing/orders | 订单列表 |
| POST | /api/v1/billing/recharge | 充值 |
| GET | /api/v1/billing/invoices | 发票列表 |

## 5. 部署架构

### 5.1 Kubernetes集群

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                      │
├─────────────────────────────────────────────────────────────┤
│  Namespace: ai-validation                                   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Ingress Controller                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│     ┌────────────────────┼────────────────────┐           │
│     ▼                    ▼                    ▼           │
│  ┌──────┐           ┌──────┐           ┌──────┐           │
│  │ API  │           │ API  │           │ API  │           │
│  │ Pod  │           │ Pod  │           │ Pod  │           │
│  └──────┘           └──────┘           └──────┘           │
│     │                    │                    │           │
│     └────────────────────┼────────────────────┘           │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Service (ClusterIP/LoadBalancer)         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │PostgreSQL│ │  Redis  │ │RabbitMQ │ │ MinIO   │          │
│  │  Statef  │ │Stateful │ │Stateful │ │Stateful │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 高可用设计

- **API服务**: 多副本 + HPA自动伸缩
- **数据库**: 主从复制 + 自动 failover
- **缓存**: Redis Cluster 或 主从
- **消息队列**: RabbitMQ 集群

## 6. 安全设计

### 6.1 认证授权

- JWT Token 认证
- 角色权限控制 (RBAC)
- 租户数据隔离
- API 限流保护

### 6.2 数据安全

- 敏感数据加密存储
- HTTPS 传输加密
- 数据定期备份
- 等保三级合规

## 7. 监控运维

### 7.1 监控指标

- 基础设施: CPU/内存/磁盘/网络
- 应用: QPS/响应时间/错误率
- 业务: 任务数/用户数/订单数

### 7.2 日志

- 统一日志收集 (ELK/Loki)
- 分布式追踪 (Jaeger)
- 异常告警 (AlertManager)

---

**版本**: V1.0  
**更新时间**: 2026-04-03  
**状态**: 架构设计中