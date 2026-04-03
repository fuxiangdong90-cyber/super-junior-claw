import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, List, Tag, Progress } from 'antd'
import { ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, CloudServerOutlined } from '@ant-design/icons'
import { taskApi } from '../services/api'

const statusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '待执行' },
  queued: { color: 'processing', text: '排队中' },
  running: { color: 'processing', text: '执行中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
  cancelled: { color: 'default', text: '已取消' },
}

export default function Dashboard() {
  const [tasks, setTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({ total: 0, running: 0, completed: 0, failed: 0 })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const response = await taskApi.list({ page: 1, page_size: 10 })
      setTasks(response.data)
      
      // 统计数据
      const total = response.data.length
      const running = response.data.filter((t: any) => t.status === 'running' || t.status === 'queued').length
      const completed = response.data.filter((t: any) => t.status === 'completed').length
      const failed = response.data.filter((t: any) => t.status === 'failed').length
      setStats({ total, running, completed, failed })
    } catch (error) {
      console.error('Failed to load tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>仪表盘</h1>
      
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="总任务数" 
              value={stats.total} 
              prefix={<ClockCircleOutlined />} 
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="执行中" 
              value={stats.running} 
              valueStyle={{ color: '#1890ff' }}
              prefix={<SyncOutlined spin />} 
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="已完成" 
              value={stats.completed} 
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />} 
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic 
              title="失败" 
              value={stats.failed} 
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<CloseCircleOutlined />} 
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="最近任务" loading={loading}>
            <List
              dataSource={tasks}
              renderItem={(task) => (
                <List.Item>
                  <List.Item.Meta
                    title={task.name}
                    description={
                      <div>
                        <Tag color={statusMap[task.status]?.color}>
                          {statusMap[task.status]?.text}
                        </Tag>
                        <span style={{ marginLeft: 8, color: '#666' }}>
                          {task.evaluation_type} / {task.evaluation_target}
                        </span>
                      </div>
                    }
                  />
                  <div>
                    <Progress 
                      percent={task.progress} 
                      size="small" 
                      style={{ width: 100 }} 
                      status={task.status === 'failed' ? 'exception' : undefined}
                    />
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="快速入口">
            <Row gutter={[8, 8]}>
              <Col span={12}>
                <Card size="small" hoverable style={{ textAlign: 'center' }}>
                  <CloudServerOutlined style={{ fontSize: 32, color: '#1890ff' }} />
                  <div style={{ marginTop: 8 }}>创建任务</div>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" hoverable style={{ textAlign: 'center' }}>
                  <CloudServerOutlined style={{ fontSize: 32, color: '#52c41a' }} />
                  <div style={{ marginTop: 8 }}>资源管理</div>
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  )
}