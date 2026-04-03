# 部署指南

## 环境要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 4核 | 8核+ |
| 内存 | 8GB | 16GB+ |
| 磁盘 | 50GB | 100GB+ SSD |
| Kubernetes | 1.24+ | 1.28+ |

## 部署方式

### 方式1: Docker Compose (开发/测试)

```bash
# 克隆项目
git clone https://github.com/fuxiangdong90-cyber/super-junior-claw.git
cd super-junior-claw

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

服务地址:
- 前端: http://localhost:3000
- 后端: http://localhost:8000
- API文档: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 方式2: Kubernetes (生产)

#### 前置条件
- Kubernetes集群 (1.24+)
- kubectl配置完成
- Ingress Controller (nginx-ingress)
- StorageClass (支持ReadWriteOnce)

#### 步骤1: 创建命名空间
```bash
kubectl create namespace ai-validation
```

#### 步骤2: 配置Secrets
编辑 `k8s/base/secrets.yaml`，修改以下内容:
```yaml
stringData:
  postgres-password: your-secure-password
  secret-key: your-jwt-secret-key
  redis-password: your-redis-password
```

#### 步骤3: 部署基础服务
```bash
kubectl apply -k k8s/base/
```

#### 步骤4: 部署应用到开发/生产环境
```bash
# 开发环境
kubectl apply -k k8s/overlays/dev/

# 生产环境
kubectl apply -k k8s/overlays/prod/
```

#### 步骤5: 验证部署
```bash
# 查看Pod状态
kubectl get pods -n ai-validation

# 查看服务
kubectl get svc -n ai-validation

# 查看Ingress
kubectl get ingress -n ai-validation
```

### 方式3: Helm Chart (推荐)

```bash
# 添加Helm仓库 (如果有)
helm repo add ai-validation https://your-repo.github.io

# 安装
helm install ai-validation ./helm \
  --namespace ai-validation \
  --create-namespace \
  --set global.imageRegistry=docker.io \
  --set backend.image.repository=your-registry/ai-validation-backend \
  --set frontend.image.repository=your-registry/ai-validation-frontend

# 升级
helm upgrade ai-validation ./helm -n ai-validation

# 删除
helm uninstall ai-validation -n ai-validation
```

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_HOST` | 数据库地址 | postgres |
| `POSTGRES_PORT` | 数据库端口 | 5432 |
| `POSTGRES_USER` | 数据库用户 | postgres |
| `POSTGRES_PASSWORD` | 数据库密码 | - |
| `POSTGRES_DB` | 数据库名称 | ai_validation |
| `REDIS_HOST` | Redis地址 | redis |
| `REDIS_PORT` | Redis端口 | 6379 |
| `SECRET_KEY` | JWT密钥 | - |
| `DEBUG` | 调试模式 | false |

### Ingress配置

生产环境需要配置TLS证书:
```yaml
spec:
  tls:
    - hosts:
        - api.aivalidation.cn
        - www.aivalidation.cn
      secretName: ai-validation-tls
```

## 监控配置

### Prometheus
```bash
# 部署Prometheus
kubectl apply -f k8s/base/prometheus-config.yaml

# 查看指标
kubectl port-forward -n ai-validation svc/prometheus 9090
```

### Grafana
```bash
# 部署Grafana
helm install grafana grafana/grafana -n monitoring

# 获取密码
kubectl get secret -n monitoring grafana -o jsonpath="{.data.admin-password}" | base64 -d
```

## 备份与恢复

### 数据库备份
```bash
# 备份
kubectl exec -n ai-validation postgres-0 -- pg_dump -U postgres ai_validation > backup.sql

# 恢复
kubectl exec -i -n ai-validation postgres-0 -- psql -U postgres ai_validation < backup.sql
```

### 持久化数据备份
```bash
# 使用Velero进行备份
velero backup create ai-validation-backup --include-namespaces ai-validation
```

## 故障排查

### 查看日志
```bash
# 后端日志
kubectl logs -n ai-validation -l app=backend -f

# 前端日志
kubectl logs -n ai-validation -l app=frontend -f

# Celery日志
kubectl logs -n ai-validation -l app=celery -f
```

### 常见问题

1. **Pod启动失败**
   ```bash
   kubectl describe pod <pod-name> -n ai-validation
   ```

2. **数据库连接失败**
   - 检查PostgreSQL是否运行
   - 验证数据库密码

3. **Ingress无法访问**
   - 检查Ingress Controller状态
   - 验证TLS证书

## 扩展

### Autoscaling
```bash
# 启用HPA
kubectl autoscale deployment backend -n ai-validation --cpu-percent=70 --min=2 --max=10
```

### 资源配额
```bash
kubectl apply -f k8s/base/resource-quota.yaml -n ai-validation
```