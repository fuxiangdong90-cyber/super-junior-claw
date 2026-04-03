import { useEffect, useState } from 'react'
import { Card, Descriptions, Timeline, Tag, Button, Space, Progress, Modal, Spin, Empty, Result } from 'antd'
import { PlayCircleOutlined, PauseCircleOutlined, StopOutlined, ReloadOutlined, CloudServerOutlined, ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { taskApi } from '../services/api'
import { useParams, useNavigate } from 'react-router-dom'

const statusMap: Record<string, { color: string; icon: any; text: string }> = {
  pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待执行' },
  queued: { color: 'processing', icon: <ClockCircleOutlined spin />, text: '排队中' },
  running: { color: 'processing', icon: <PlayCircleOutlined spin />, text: '执行中' },
  completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
  cancelled: { color: 'default', icon: <StopOutlined />, text: '已取消' },
}

const priorityMap: Record<string, { color: string; text: string }> = {
  low: { color: 'green', text: '低' },
  medium: { color: 'blue', text: '中' },
  high: { color: 'orange', text: '高' },
  urgent: { color: 'red', text: '紧急' },
}

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [task, setTask] = useState<any>(null)
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [logModalVisible, setLogModalVisible] = useState(false)

  useEffect(() => {
    if (id) loadTask(id)
  }, [id])

  const loadTask = async (taskId: string) => {
    setLoading(true)
    try {
      const [taskRes, logsRes] = await Promise.all([
        taskApi.get(taskId),
        taskApi.getLogs(taskId),
      ])
      setTask(taskRes.data)
      setLogs(logsRes.data)
    } catch (error) {
      console.error('Failed to load task:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async () => {
    try {
      await taskApi.update(id!, { status: 'cancelled' })
      loadTask(id!)
    } catch (error) {
      console.error('Failed to cancel task:', error)
    }
  }

  const handleRetry = async () => {
    try {
      await taskApi.update(id!, { status: 'pending' })
      loadTask(id!)
    } catch (error) {
      console.error('Failed to retry task:', error)
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!task) {
    return <Empty description="任务不存在" />
  }

  const status = statusMap[task.status] || statusMap.pending
  const priority = priorityMap[task.priority] || priorityMap.medium

  return (
    <div style={{ padding: 24 }}>
      {/* 顶部状态卡片 */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: 0 }}>{task.name}</h2>
            <Space style={{ marginTop: 8 }}>
              <Tag color={status.color} icon={status.icon}>{status.text}</Tag>
              <Tag color={priority.color}>{priority.text}</Tag>
              <Tag>{task.evaluation_type} / {task.evaluation_target}</Tag>
            </Space>
          </div>
          <Space>
            {task.status === 'running' && (
              <Button icon={<StopOutlined />} danger onClick={handleCancel}>取消任务</Button>
            )}
            {(task.status === 'failed' || task.status === 'cancelled') && (
              <Button type="primary" icon={<ReloadOutlined />} onClick={handleRetry}>重新执行</Button>
            )}
            <Button onClick={() => setLogModalVisible(true)}>查看日志</Button>
          </Space>
        </div>

        {/* 进度条 */}
        <div style={{ marginTop: 24 }}>
          <Progress 
            percent={task.progress} 
            status={task.status === 'failed' ? 'exception' : task.status === 'completed' ? 'success' : 'active'}
            strokeColor={task.status === 'failed' ? '#ff4d4f' : '#1890ff'}
          />
        </div>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* 基本信息 */}
        <Card title="任务信息">
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="任务ID">{task.id}</Descriptions.Item>
            <Descriptions.Item label="评测类型">{task.evaluation_type}</Descriptions.Item>
            <Descriptions.Item label="评测对象">{task.evaluation_target}</Descriptions.Item>
            <Descriptions.Item label="优先级">{priority.text}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{new Date(task.created_at).toLocaleString('zh-CN')}</Descriptions.Item>
            {task.started_at && (
              <Descriptions.Item label="开始时间">{new Date(task.started_at).toLocaleString('zh-CN')}</Descriptions.Item>
            )}
            {task.finished_at && (
              <Descriptions.Item label="完成时间">{new Date(task.finished_at).toLocaleString('zh-CN')}</Descriptions.Item>
            )}
          </Descriptions>
        </Card>

        {/* 资源配置 */}
        <Card title="资源配置">
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="GPU数量">{task.required_gpu_count}</Descriptions.Item>
            {task.required_gpu_model && (
              <Descriptions.Item label="GPU型号">{task.required_gpu_model}</Descriptions.Item>
            )}
            <Descriptions.Item label="内存">{task.required_memory_gb} GB</Descriptions.Item>
            {task.allocated_resource_id && (
              <Descriptions.Item label="分配资源">
                <Tag icon={<CloudServerOutlined />}>{task.allocated_resource_id}</Tag>
              </Descriptions.Item>
            )}
          </Descriptions>
        </Card>

        {/* 计费信息 */}
        <Card title="计费信息">
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="任务类型">
              <Tag color={task.is_custom ? 'orange' : 'green'}>
                {task.is_custom ? '自定义评测(收费)' : '标准评测(免费)'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="预估费用">¥{(task.estimated_cost / 100).toFixed(2)}</Descriptions.Item>
            <Descriptions.Item label="实际费用">¥{(task.actual_cost / 100).toFixed(2)}</Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 错误信息 */}
        {task.error_message && (
          <Card title="错误信息" bordered>
            <Alert 
              message="任务执行失败" 
              description={task.error_message} 
              type="error" 
              showIcon 
            />
          </Card>
        )}
      </div>

      {/* 评测结果 */}
      {task.result && task.status === 'completed' && (
        <Card title="评测结果" style={{ marginTop: 16 }}>
          <pre style={{ background: '#f5f5f5', padding: 16, borderRadius: 8, overflow: 'auto' }}>
            {JSON.stringify(task.result, null, 2)}
          </pre>
        </Card>
      )}

      {/* 日志弹窗 */}
      <Modal
        title="任务日志"
        open={logModalVisible}
        onCancel={() => setLogModalVisible(false)}
        width={800}
        footer={null}
      >
        <Timeline>
          {logs.map((log, index) => (
            <Timeline.Item 
              key={index}
              color={log.level === 'ERROR' ? 'red' : log.level === 'WARNING' ? 'orange' : 'blue'}
            >
              <p style={{ margin: 0 }}>{log.message}</p>
              <small style={{ color: '#999' }}>{new Date(log.created_at).toLocaleString('zh-CN')}</small>
            </Timeline.Item>
          ))}
        </Timeline>
        {logs.length === 0 && <Empty description="暂无日志" />}
      </Modal>
    </div>
  )
}

import { Alert } from 'antd'