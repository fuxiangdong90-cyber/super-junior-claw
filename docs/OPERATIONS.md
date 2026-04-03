# 运维手册

## 日常运维

### 检查服务状态
```bash
# 查看所有Pod
kubectl get pods -n ai-validation

# 查看服务
kubectl get svc -n ai-validation

# 查看资源使用
kubectl top pods -n ai-validation
```

### 查看日志
```bash
# 后端实时日志
kubectl logs -n ai-validation -l app=backend -f --tail=100

# 前端日志
kubectl logs -n ai-validation -l app=frontend -f --tail=100

# 搜索错误
kubectl logs -n ai-validation -l app=backend | grep -i error
```

### 重启服务
```bash
# 重启后端
kubectl rollout restart deployment/backend -n ai-validation

# 重启前端
kubectl rollout restart deployment/frontend -n ai-validation

# 查看重启状态
kubectl rollout status deployment/backend -n ai-validation
```

## 扩容缩容

### 手动扩容
```bash
# 扩容后端到5个副本
kubectl scale deployment/backend -n ai-validation --replicas=5

# 扩容前端到3个副本
kubectl scale deployment/frontend -n ai-validation --replicas=3
```

### 自动扩容 (HPA)
```bash
# 启用HPA
kubectl autoscale deployment backend -n ai-validation \
  --cpu-percent=70 --min=2 --max=10

# 查看HPA状态
kubectl get hpa -n ai-validation
```

## 监控告警

### Prometheus
```bash
# 端口转发访问Prometheus
kubectl port-forward -n ai-validation svc/prometheus 9090

# 访问 http://localhost:9090
```

### Grafana
```bash
# 获取Grafana密码
kubectl get secret -n monitoring grafana \
  -o jsonpath="{.data.admin-password}" | base64 -d

# 端口转发
kubectl port-forward -n monitoring svc/grafana 3000

# 访问 http://localhost:3000
```

### 查看告警
```bash
# 查看当前告警
kubectl get alerts -n monitoring

# 查看Prometheus告警规则
kubectl get prometheusrules -n ai-validation
```

## 数据库操作

### 备份
```bash
# 手动备份数据库
kubectl exec -n ai-validation postgres-0 -- \
  pg_dump -U postgres ai_validation > backup_$(date +%Y%m%d).sql
```

### 恢复
```bash
# 恢复数据库
kubectl exec -i -n ai-validation postgres-0 -- \
  psql -U postgres ai_validation < backup_20260401.sql
```

## 常见问题

### Pod启动失败
```bash
# 查看详细事件
kubectl describe pod <pod-name> -n ai-validation

# 常见原因：
# 1. 镜像拉取失败 -> 检查镜像地址
# 2. 资源配置不足 -> 增加资源限制
# 3. 依赖服务未就绪 -> 检查依赖服务
```

### 数据库连接失败
```bash
# 检查PostgreSQL状态
kubectl get pods -n ai-validation -l app=postgres

# 测试连接
kubectl exec -it -n ai-validation backend-xxx -- \
  nc -zv postgres 5432

# 查看数据库日志
kubectl logs -n ai-validation postgres-0
```

### 磁盘空间不足
```bash
# 查看磁盘使用
kubectl top nodes

# 清理不必要的资源
kubectl delete pods -n ai-validation --field-selector=status.phase=Succeeded

# 清理镜像
kubectl delete pod -n ai-validation -l app=cleanup
```

## 更新升级

### 更新应用
```bash
# 更新镜像版本
kubectl set image deployment/backend backend=ai-validation-backend:v1.1.0 -n ai-validation
kubectl set image deployment/frontend frontend=ai-validation-frontend:v1.1.0 -n ai-validation

# 查看更新状态
kubectl rollout status deployment/backend -n ai-validation
```

### 回滚
```bash
# 回滚到上一个版本
kubectl rollout undo deployment/backend -n ai-validation

# 回滚到指定版本
kubectl rollout undo deployment/backend -n ai-validation --to-revision=3
```

## 安全

### 更新Secrets
```bash
# 编辑密钥
kubectl edit secret ai-validation-secrets -n ai-validation

# Base64编码新值
echo -n "newpassword" | base64
```

### 检查安全漏洞
```bash
# 使用trivy扫描镜像
trivy image ai-validation-backend:latest

# 使用kube-bench检查K8s安全
kube-bench run --targets=master
```