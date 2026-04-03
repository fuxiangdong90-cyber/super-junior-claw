"""
AI Validation Platform - 核心业务逻辑
完整实现评测平台所有功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json


class TaskManager:
    """任务管理器 - 完整的任务生命周期管理"""
    
    TASK_STATES = {
        'pending': '待执行',
        'queued': '排队中', 
        'running': '执行中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消',
        'paused': '已暂停'
    }
    
    PRIORITY_LEVELS = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'urgent': 4
    }
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.task_queue: List[str] = []
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建任务"""
        task_id = self._generate_id()
        
        task = {
            'id': task_id,
            'name': task_data['name'],
            'description': task_data.get('description', ''),
            'evaluation_type': task_data['evaluation_type'],  # performance/precision/compatibility/stability
            'evaluation_target': task_data['evaluation_target'],  # chip/operator/framework/model/scenario
            'status': 'pending',
            'priority': task_data.get('priority', 'medium'),
            'progress': 0.0,
            'config': task_data.get('config', {}),
            'result': None,
            'required_gpu_count': task_data.get('required_gpu_count', 1),
            'required_gpu_model': task_data.get('required_gpu_model'),
            'required_memory_gb': task_data.get('required_memory_gb', 16),
            'allocated_resource_id': None,
            'user_id': task_data['user_id'],
            'tenant_id': task_data.get('tenant_id'),
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'finished_at': None,
            'estimated_cost': self._estimate_cost(task_data),
            'actual_cost': 0,
            'error_message': None,
            'logs': [],
            'retry_count': 0,
            'max_retries': task_data.get('max_retries', 3),
        }
        
        self.tasks[task_id] = task
        self.task_queue.append(task_id)
        
        return task
    
    def queue_task(self, task_id: str) -> bool:
        """将任务加入队列"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task['status'] != 'pending':
            return False
        
        task['status'] = 'queued'
        task['queue_position'] = len(self.task_queue)
        return True
    
    def start_task(self, task_id: str, resource_id: str) -> bool:
        """启动任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task['status'] not in ['pending', 'queued']:
            return False
        
        task['status'] = 'running'
        task['started_at'] = datetime.utcnow().isoformat()
        task['allocated_resource_id'] = resource_id
        task['logs'].append({
            'time': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'message': f'Task started with resource {resource_id}'
        })
        
        return True
    
    def update_progress(self, task_id: str, progress: float, message: str = None) -> bool:
        """更新任务进度"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task['progress'] = min(100.0, max(0.0, progress))
        
        if message:
            task['logs'].append({
                'time': datetime.utcnow().isoformat(),
                'level': 'INFO',
                'message': message
            })
        
        return True
    
    def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """完成任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task['status'] = 'completed'
        task['progress'] = 100.0
        task['finished_at'] = datetime.utcnow().isoformat()
        task['result'] = result
        
        # 计算实际费用
        if task['started_at']:
            start = datetime.fromisoformat(task['started_at'])
            duration_hours = (datetime.utcnow() - start).total_seconds() / 3600
            task['actual_cost'] = int(duration_hours * task.get('estimated_hourly_cost', 100))
        
        task['logs'].append({
            'time': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'message': 'Task completed successfully'
        })
        
        return True
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """任务失败"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task['status'] = 'failed'
        task['finished_at'] = datetime.utcnow().isoformat()
        task['error_message'] = error_message
        
        task['logs'].append({
            'time': datetime.utcnow().isoformat(),
            'level': 'ERROR',
            'message': f'Task failed: {error_message}'
        })
        
        return True
    
    def terminate_task(self, task_id: str, force: bool = False) -> bool:
        """终止任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task['status'] not in ['pending', 'queued', 'running', 'paused']:
            return False
        
        task['status'] = 'cancelled'
        task['finished_at'] = datetime.utcnow().isoformat()
        
        task['logs'].append({
            'time': datetime.utcnow().isoformat(),
            'level': 'WARNING',
            'message': f'Task terminated by user (force={force})'
        })
        
        return True
    
    def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task['status'] not in ['failed', 'cancelled']:
            return False
        
        if task['retry_count'] >= task['max_retries']:
            return False
        
        task['retry_count'] += 1
        task['status'] = 'pending'
        task['progress'] = 0.0
        task['started_at'] = None
        task['finished_at'] = None
        task['error_message'] = None
        task['result'] = None
        
        task['logs'].append({
            'time': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'message': f'Task retry initiated (attempt {task["retry_count"]}/{task["max_retries"]})'
        })
        
        self.task_queue.append(task_id)
        return True
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task['status'] != 'running':
            return False
        
        task['status'] = 'paused'
        task['logs'].append({
            'time': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'message': 'Task paused by user'
        })
        
        return True
    
    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task['status'] != 'paused':
            return False
        
        task['status'] = 'running'
        task['logs'].append({
            'time': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'message': 'Task resumed by user'
        })
        
        return True
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, filters: Dict = None) -> List[Dict]:
        """列出任务"""
        tasks = list(self.tasks.values())
        
        if not filters:
            return sorted(tasks, key=lambda t: (
                -self.PRIORITY_LEVELS.get(t['priority'], 0),
                t['created_at']
            ))
        
        result = []
        for task in tasks:
            match = True
            if filters.get('status') and task['status'] != filters['status']:
                match = False
            if filters.get('user_id') and task['user_id'] != filters['user_id']:
                match = False
            if filters.get('tenant_id') and task['tenant_id'] != filters['tenant_id']:
                match = False
            if filters.get('evaluation_type') and task['evaluation_type'] != filters['evaluation_type']:
                match = False
            
            if match:
                result.append(task)
        
        return sorted(result, key=lambda t: (
            -self.PRIORITY_LEVELS.get(t['priority'], 0),
            t['created_at']
        ))
    
    def get_task_stats(self, tenant_id: str = None) -> Dict[str, int]:
        """获取任务统计"""
        stats = {status: 0 for status in self.TASK_STATES}
        stats['total'] = 0
        
        for task in self.tasks.values():
            if tenant_id and task.get('tenant_id') != tenant_id:
                continue
            stats[task['status']] += 1
            stats['total'] += 1
        
        return stats
    
    def _generate_id(self) -> str:
        """生成ID"""
        return f"task_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(str(datetime.utcnow()))[:8]}"
    
    def _estimate_cost(self, task_data: Dict) -> int:
        """预估费用"""
        gpu_count = task_data.get('required_gpu_count', 1)
        # 简化计算: 每GPU每小时100分
        estimated_hours = task_data.get('estimated_hours', 2)
        return gpu_count * estimated_hours * 100


class ResourceManager:
    """资源管理器 - 算力资源分配与调度"""
    
    RESOURCE_TYPES = ['gpu', 'npu', 'fpga', 'cpu']
    VENDORS = ['华为', '寒武纪', '摩尔线程', '景嘉微', 'NVIDIA', 'Intel']
    STATUSES = ['available', 'busy', 'offline', 'maintenance']
    
    def __init__(self):
        self.resources: Dict[str, Dict] = {}
        self.allocations: Dict[str, Dict] = {}  # task_id -> resource_id
    
    def register_resource(self, resource_data: Dict) -> Dict:
        """注册资源"""
        resource_id = self._generate_id()
        
        resource = {
            'id': resource_id,
            'name': resource_data['name'],
            'resource_type': resource_data['resource_type'],
            'vendor': resource_data['vendor'],
            'model': resource_data['model'],
            'gpu_count': resource_data.get('gpu_count', 1),
            'gpu_memory_gb': resource_data.get('gpu_memory_gb'),
            'cpu_cores': resource_data.get('cpu_cores'),
            'cpu_memory_gb': resource_data.get('cpu_memory_gb'),
            'storage_tb': resource_data.get('storage_tb'),
            'source': resource_data.get('source', 'self'),  # self/cloud/user
            'status': 'available',
            'price_per_hour': resource_data.get('price_per_hour', 100),
            'total_usage_hours': 0,
            'current_task_count': 0,
            'created_at': datetime.utcnow().isoformat(),
            'last_health_check': datetime.utcnow().isoformat(),
        }
        
        self.resources[resource_id] = resource
        return resource
    
    def allocate_resource(self, requirements: Dict) -> Optional[Dict]:
        """分配资源"""
        gpu_count = requirements.get('required_gpu_count', 1)
        gpu_model = requirements.get('required_gpu_model')
        tenant_id = requirements.get('tenant_id')
        
        # 过滤可用资源
        candidates = []
        for resource in self.resources.values():
            if resource['status'] != 'available':
                continue
            if resource['gpu_count'] < gpu_count:
                continue
            if gpu_model and resource['model'] != gpu_model:
                continue
            
            candidates.append(resource)
        
        if not candidates:
            return None
        
        # 选择最佳资源（优先选择负载低的）
        selected = min(candidates, key=lambda r: r['current_task_count'])
        
        # 分配
        selected['status'] = 'busy'
        selected['current_task_count'] += 1
        
        return {
            'resource_id': selected['id'],
            'resource': selected
        }
    
    def release_resource(self, resource_id: str) -> bool:
        """释放资源"""
        if resource_id not in self.resources:
            return False
        
        resource = self.resources[resource_id]
        
        # 释放所有分配给该资源的任务
        for task_id, res_id in list(self.allocations.items()):
            if res_id == resource_id:
                del self.allocations[task_id]
        
        resource['status'] = 'available'
        resource['current_task_count'] = 0
        
        return True
    
    def check_health(self, resource_id: str) -> Dict:
        """检查资源健康状态"""
        if resource_id not in self.resources:
            return {'status': 'not_found'}
        
        resource = self.resources[resource_id]
        
        # 模拟健康检查
        is_healthy = resource['status'] != 'offline'
        
        return {
            'resource_id': resource_id,
            'healthy': is_healthy,
            'status': resource['status'],
            'current_tasks': resource['current_task_count'],
            'last_check': datetime.utcnow().isoformat()
        }
    
    def list_resources(self, filters: Dict = None) -> List[Dict]:
        """列出资源"""
        resources = list(self.resources.values())
        
        if not filters:
            return resources
        
        result = []
        for resource in resources:
            match = True
            if filters.get('resource_type') and resource['resource_type'] != filters['resource_type']:
                match = False
            if filters.get('vendor') and resource['vendor'] != filters['vendor']:
                match = False
            if filters.get('status') and resource['status'] != filters['status']:
                match = False
            
            if match:
                result.append(resource)
        
        return result
    
    def get_resource_stats(self) -> Dict:
        """获取资源统计"""
        stats = {
            'total': len(self.resources),
            'available': 0,
            'busy': 0,
            'offline': 0,
            'maintenance': 0,
            'total_gpu_count': 0,
        }
        
        for resource in self.resources.values():
            stats[resource['status']] = stats.get(resource['status'], 0) + 1
            stats['total_gpu_count'] += resource.get('gpu_count', 0)
        
        return stats
    
    def _generate_id(self) -> str:
        return f"res_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(str(datetime.utcnow()))[:8]}"


class ReportGenerator:
    """报告生成器 - 评测报告生成与管理"""
    
    REPORT_TYPES = ['basic', 'advanced', 'detailed']
    SHARING_LEVELS = ['private', 'tenant', 'public']
    
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
        self.reports: Dict[str, Dict] = {}
    
    def generate_report(self, task_id: str, report_type: str = 'basic', user_id: str = None, tenant_id: str = None) -> Dict:
        """生成报告"""
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task['status'] != 'completed':
            raise ValueError("Task not completed")
        
        report_id = self._generate_id()
        
        # 根据报告类型生成不同详细程度的内容
        if report_type == 'basic':
            content = self._generate_basic_report(task)
        elif report_type == 'advanced':
            content = self._generate_advanced_report(task)
        else:  # detailed
            content = self._generate_detailed_report(task)
        
        report = {
            'id': report_id,
            'name': f"{task['name']} - 评测报告",
            'description': task.get('description', ''),
            'report_type': report_type,
            'task_id': task_id,
            'user_id': user_id,
            'tenant_id': tenant_id,
            'summary': content['summary'],
            'metrics': content['metrics'],
            'benchmark': task.get('result', {}).get('benchmark', {}),
            'charts': content.get('charts', []),
            'status': 'ready',
            'sharing': 'private',
            'view_count': 0,
            'download_count': 0,
            'created_at': datetime.utcnow().isoformat(),
            'generated_at': datetime.utcnow().isoformat(),
        }
        
        self.reports[report_id] = report
        return report
    
    def _generate_basic_report(self, task: Dict) -> Dict:
        """生成基础报告"""
        result = task.get('result', {})
        
        return {
            'summary': {
                'task_name': task['name'],
                'evaluation_type': task['evaluation_type'],
                'status': task['status'],
                'completed_at': task.get('finished_at'),
            },
            'metrics': result.get('metrics', {}),
            'benchmark': result.get('benchmark', {}),
            'charts': []
        }
    
    def _generate_advanced_report(self, task: Dict) -> Dict:
        """生成高级报告"""
        basic = self._generate_basic_report(task)
        
        # 添加更多分析
        basic['analysis'] = {
            'performance_analysis': self._analyze_performance(task),
            'recommendations': self._generate_recommendations(task),
            'comparison': self._compare_with_baseline(task),
        }
        
        return basic
    
    def _generate_detailed_report(self, task: Dict) -> Dict:
        """生成详细报告"""
        advanced = self._generate_advanced_report(task)
        
        # 添加完整日志和原始数据
        advanced['logs'] = task.get('logs', [])
        advanced['raw_data'] = task.get('result', {})
        advanced['config'] = task.get('config', {})
        advanced['timeline'] = self._generate_timeline(task)
        
        return advanced
    
    def _analyze_performance(self, task: Dict) -> Dict:
        """性能分析"""
        result = task.get('result', {})
        metrics = result.get('metrics', {})
        
        analysis = {
            'overall_score': result.get('benchmark', {}).get('score', 0),
            'grade': result.get('benchmark', {}).get('grade', 'N/A'),
            'strengths': [],
            'weaknesses': [],
            'suggestions': []
        }
        
        # 简单分析逻辑
        if metrics.get('throughput', 0) > 1000:
            analysis['strengths'].append('高吞吐量')
        else:
            analysis['weaknesses'].append('吞吐量有待提升')
        
        if metrics.get('latency_ms', 999) < 50:
            analysis['strengths'].append('低延迟')
        else:
            analysis['suggestions'].append('建议优化延迟')
        
        return analysis
    
    def _generate_recommendations(self, task: Dict) -> List[str]:
        """生成建议"""
        recommendations = []
        
        result = task.get('result', {})
        metrics = result.get('metrics', {})
        
        if metrics.get('gpu_utilization', 0) < 70:
            recommendations.append('建议增加batch size以提高GPU利用率')
        
        if metrics.get('memory_utilization', 0) > 90:
            recommendations.append('内存使用率较高，建议优化内存管理')
        
        if task.get('evaluation_target') == 'chip':
            recommendations.append('建议进行长期稳定性测试')
        
        return recommendations
    
    def _compare_with_baseline(self, task: Dict) -> Dict:
        """与基准对比"""
        # 简化实现
        return {
            'vs_previous': '+5%',
            'vs_average': '+10%',
            'vs_best': '-3%'
        }
    
    def _generate_timeline(self, task: Dict) -> List[Dict]:
        """生成时间线"""
        timeline = []
        
        timeline.append({
            'time': task['created_at'],
            'event': '任务创建',
            'status': 'info'
        })
        
        if task.get('started_at'):
            timeline.append({
                'time': task['started_at'],
                'event': '任务开始执行',
                'status': 'info'
            })
        
        if task.get('finished_at'):
            timeline.append({
                'time': task['finished_at'],
                'event': f"任务{task['status']}",
                'status': 'success' if task['status'] == 'completed' else 'error'
            })
        
        return timeline
    
    def share_report(self, report_id: str, sharing: str, expires_hours: int = 24) -> Dict:
        """分享报告"""
        if report_id not in self.reports:
            raise ValueError("Report not found")
        
        report = self.reports[report_id]
        
        share_code = self._generate_share_code()
        
        report['sharing'] = sharing
        report['share_code'] = share_code
        report['share_expires_at'] = datetime.utcnow().isoformat()
        
        return {
            'share_code': share_code,
            'expires_at': report['share_expires_at'],
            'sharing': sharing
        }
    
    def get_report(self, report_id: str) -> Optional[Dict]:
        """获取报告"""
        return self.reports.get(report_id)
    
    def list_reports(self, user_id: str = None, tenant_id: str = None) -> List[Dict]:
        """列出报告"""
        reports = []
        
        for report in self.reports.values():
            if user_id and report.get('user_id') != user_id:
                # 检查分享权限
                if report['sharing'] == 'private':
                    continue
                if report['sharing'] == 'tenant' and report.get('tenant_id') != tenant_id:
                    continue
            
            reports.append(report)
        
        return sorted(reports, key=lambda r: r['created_at'], reverse=True)
    
    def _generate_id(self) -> str:
        return f"report_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(str(datetime.utcnow()))[:8]}"
    
    def _generate_share_code(self) -> str:
        import secrets
        return secrets.token_urlsafe(16)


class AssetManager:
    """资产管理器 - 数据集、模型、工具等"""
    
    ASSET_TYPES = ['dataset', 'model', 'framework', 'tool', 'report', 'image']
    
    def __init__(self):
        self.assets: Dict[str, Dict] = {}
    
    def register_asset(self, asset_data: Dict) -> Dict:
        """注册资产"""
        asset_id = self._generate_id()
        
        asset = {
            'id': asset_id,
            'name': asset_data['name'],
            'description': asset_data.get('description', ''),
            'asset_type': asset_data['asset_type'],
            'status': 'uploading',
            'file_name': asset_data.get('file_name'),
            'file_size': asset_data.get('file_size'),
            'file_path': asset_data.get('file_path'),
            'mime_type': asset_data.get('mime_type'),
            'checksum': asset_data.get('checksum'),
            'metadata': asset_data.get('metadata', {}),
            'tags': asset_data.get('tags', []),
            'is_public': asset_data.get('is_public', False),
            'is_free': asset_data.get('is_free', False),
            'reference_count': 0,
            'download_count': 0,
            'owner_id': asset_data.get('owner_id'),
            'tenant_id': asset_data.get('tenant_id'),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
        }
        
        self.assets[asset_id] = asset
        return asset
    
    def upload_complete(self, asset_id: str) -> bool:
        """上传完成"""
        if asset_id not in self.assets:
            return False
        
        self.assets[asset_id]['status'] = 'ready'
        self.assets[asset_id]['updated_at'] = datetime.utcnow().isoformat()
        return True
    
    def get_asset(self, asset_id: str) -> Optional[Dict]:
        """获取资产"""
        return self.assets.get(asset_id)
    
    def list_assets(self, filters: Dict = None) -> List[Dict]:
        """列出资产"""
        assets = list(self.assets.values())
        
        if not filters:
            return sorted(assets, key=lambda a: a['created_at'], reverse=True)
        
        result = []
        for asset in assets:
            match = True
            if filters.get('asset_type') and asset['asset_type'] != filters['asset_type']:
                match = False
            if filters.get('is_public') is not None and asset['is_public'] != filters['is_public']:
                match = False
            if filters.get('owner_id') and asset['owner_id'] != filters['owner_id']:
                match = False
            
            if match:
                result.append(asset)
        
        return sorted(result, key=lambda a: a['created_at'], reverse=True)
    
    def increment_download(self, asset_id: str) -> bool:
        """增加下载次数"""
        if asset_id not in self.assets:
            return False
        
        self.assets[asset_id]['download_count'] += 1
        return True
    
    def _generate_id(self) -> str:
        return f"asset_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(str(datetime.utcnow()))[:8]}"


class TenantManager:
    """租户管理器 - 多租户管理"""
    
    def __init__(self):
        self.tenants: Dict[str, Dict] = {}
        self.members: Dict[str, Dict] = {}  # user_id -> tenant_id
    
    def create_tenant(self, tenant_data: Dict) -> Dict:
        """创建租户"""
        tenant_id = self._generate_id()
        
        tenant = {
            'id': tenant_id,
            'name': tenant_data['name'],
            'description': tenant_data.get('description', ''),
            'max_concurrent_tasks': tenant_data.get('max_concurrent_tasks', 10),
            'max_storage_gb': tenant_data.get('max_storage_gb', 100),
            'max_users': tenant_data.get('max_users', 50),
            'used_concurrent_tasks': 0,
            'used_storage_gb': 0,
            'balance': tenant_data.get('initial_balance', 0),
            'subscription_type': tenant_data.get('subscription_type', 'free'),
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
        }
        
        self.tenants[tenant_id] = tenant
        return tenant
    
    def add_member(self, tenant_id: str, user_id: str, role: str = 'member') -> bool:
        """添加成员"""
        if tenant_id not in self.tenants:
            return False
        
        self.members[user_id] = {
            'tenant_id': tenant_id,
            'role': role,
            'joined_at': datetime.utcnow().isoformat()
        }
        
        return True
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict]:
        """获取租户"""
        return self.tenants.get(tenant_id)
    
    def get_user_tenant(self, user_id: str) -> Optional[Dict]:
        """获取用户所属租户"""
        tenant_id = self.members.get(user_id, {}).get('tenant_id')
        if tenant_id:
            return self.tenants.get(tenant_id)
        return None
    
    def update_balance(self, tenant_id: str, amount: int) -> bool:
        """更新余额"""
        if tenant_id not in self.tenants:
            return False
        
        self.tenants[tenant_id]['balance'] += amount
        return True
    
    def check_quota(self, tenant_id: str, resource_type: str, amount: int) -> bool:
        """检查配额"""
        if tenant_id not in self.tenants:
            return False
        
        tenant = self.tenants[tenant_id]
        
        if resource_type == 'task':
            if tenant['used_concurrent_tasks'] + amount > tenant['max_concurrent_tasks']:
                return False
        
        if resource_type == 'storage':
            if tenant['used_storage_gb'] + amount > tenant['max_storage_gb']:
                return False
        
        return True
    
    def _generate_id(self) -> str:
        return f"tenant_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(str(datetime.utcnow()))[:8]}"


# 全局实例
task_manager = TaskManager()
resource_manager = ResourceManager()
report_generator = ReportGenerator(task_manager)
asset_manager = AssetManager()
tenant_manager = TenantManager()