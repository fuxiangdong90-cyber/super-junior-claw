export interface User {
  id: string
  email: string
  username: string
  full_name?: string
  role: 'admin' | 'tenant_admin' | 'user' | 'guest'
  status: 'active' | 'inactive' | 'pending' | 'banned'
  is_active: boolean
  is_superuser: boolean
  tenant_id?: string
  created_at: string
  last_login?: string
}

export interface Tenant {
  id: string
  name: string
  description?: string
  status: 'active' | 'inactive' | 'pending' | 'banned'
  max_concurrent_tasks: number
  max_storage_gb: number
  used_concurrent_tasks: number
  used_storage_gb: number
  balance: number
  subscription_type: string
  created_at: string
}

export interface EvaluationTask {
  id: string
  name: string
  description?: string
  evaluation_type: 'performance' | 'precision' | 'compatibility' | 'stability'
  evaluation_target: 'chip' | 'operator' | 'framework' | 'model' | 'scenario'
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  progress: number
  config?: Record<string, any>
  result?: Record<string, any>
  required_gpu_count: number
  required_gpu_model?: string
  required_memory_gb: number
  allocated_resource_id?: string
  queue_position: number
  estimated_start_time?: string
  started_at?: string
  finished_at?: string
  is_custom: boolean
  estimated_cost: number
  actual_cost: number
  error_message?: string
  error_detail?: Record<string, any>
  user_id: string
  tenant_id?: string
  dataset_id?: string
  tool_id?: string
  created_at: string
  updated_at: string
}

export interface Asset {
  id: string
  name: string
  description?: string
  asset_type: 'dataset' | 'model' | 'framework' | 'tool' | 'report' | 'image'
  status: 'uploading' | 'ready' | 'processing' | 'failed' | 'deleted'
  file_name?: string
  file_size?: number
  file_path?: string
  mime_type?: string
  checksum?: string
  metadata?: Record<string, any>
  tags?: string[]
  reference_count: number
  is_public: boolean
  is_free: boolean
  download_count: number
  owner_id?: string
  tenant_id?: string
  created_at: string
  updated_at: string
}

export interface ComputeResource {
  id: string
  name: string
  description?: string
  resource_type: string
  vendor: string
  model: string
  gpu_count: number
  gpu_memory_gb?: number
  cpu_cores?: number
  cpu_memory_gb?: number
  storage_tb?: number
  source: 'self' | 'cloud' | 'user'
  cloud_provider?: string
  cloud_region?: string
  cloud_instance_id?: string
  status: string
  is_active: boolean
  total_usage_hours: number
  current_task_count: number
  tenant_id?: string
  price_per_hour: number
  created_at: string
  updated_at: string
}