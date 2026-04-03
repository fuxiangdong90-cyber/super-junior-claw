import { useEffect, useState } from 'react'
import { Table, Tag, Card, Row, Col, Progress, message, Button, Space } from 'antd'
import { CloudServerOutlined } from '@ant-design/icons'
import { resourceApi } from '../services/api'

const vendorMap: Record<string, { color: string }> = {
  '华为': { color: '#cf1322' },
  '寒武纪': { color: '#389e0d' },
  '摩尔线程': { color: '#096dd9' },
  '景嘉微': { color: '#d4380d' },
  'Intel': { color: '#1d39c4' },
  'NVIDIA': { color: '#76b852' },
}

const statusMap: Record<string, { color: string; text: string }> = {
  available: { color: 'success', text: '可用' },
  busy: { color: 'warning', text: '使用中' },
  offline: { color: 'default', text: '离线' },
  maintenance: { color: 'processing', text: '维护中' },
}

export default function Resources() {
  const [resources, setResources] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadResources()
  }, [])

  const loadResources = async () => {
    try {
      const response = await resourceApi.list()
      setResources(response.data)
    } catch (error) {
      message.error('加载资源失败')
    } finally {
      setLoading(false)
    }
  }

  const stats = {
    total: resources.length,
    available: resources.filter(r => r.status === 'available').length,
    busy: resources.filter(r => r.status === 'busy').length,
    gpuCount: resources.reduce((sum, r) => sum + (r.gpu_count || 0), 0),
  }

  const columns = [
    { 
      title: '资源名称', 
      dataIndex: 'name', 
      key: 'name',
      render: (name: string, record: any) => (
        <Space>
          <CloudServerOutlined style={{ color: vendorMap[record.vendor]?.color || '#666' }} />
          {name}
        </Space>
      )
    },
    { 
      title: '厂商', 
      dataIndex: 'vendor', 
      key: 'vendor',
      render: (vendor: string) => <Tag color={vendorMap[vendor]?.color}>{vendor}</Tag>
    },
    { title: '型号', dataIndex: 'model', key: 'model' },
    { 
      title: '类型', 
      dataIndex: 'resource_type', 
      key: 'resource_type',
      render: (type: string) => <Tag>{type.toUpperCase()}</Tag>
    },
    { title: 'GPU数量', dataIndex: 'gpu_count', key: 'gpu_count' },
    { title: 'GPU显存(GB)', dataIndex: 'gpu_memory_gb', key: 'gpu_memory_gb' },
    { title: 'CPU核数', dataIndex: 'cpu_cores', key: 'cpu_cores' },
    { title: '内存(GB)', dataIndex: 'cpu_memory_gb', key: 'cpu_memory_gb' },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => (
        <Tag color={statusMap[status]?.color}>{statusMap[status]?.text}</Tag>
      )
    },
    { 
      title: '来源', 
      dataIndex: 'source', 
      key: 'source',
      render: (source: string) => {
        const map: Record<string, string> = { self: '平台自有', cloud: '云厂商', user: '用户' }
        return <Tag>{map[source] || source}</Tag>
      }
    },
    { 
      title: '单价(元/时)', 
      dataIndex: 'price_per_hour', 
      key: 'price_per_hour',
      render: (price: number) => (price / 100).toFixed(2)
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>算力资源</h1>
      
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Card.Meta 
              title="总资源数" 
              description={<span style={{ fontSize: 24, fontWeight: 'bold' }}>{stats.total}</span>} 
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Card.Meta 
              title="可用资源" 
              description={<span style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>{stats.available}</span>} 
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Card.Meta 
              title="使用中" 
              description={<span style={{ fontSize: 24, fontWeight: 'bold', color: '#faad14' }}>{stats.busy}</span>} 
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Card.Meta 
              title="GPU总数" 
              description={<span style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>{stats.gpuCount}</span>} 
            />
          </Card>
        </Col>
      </Row>

      <Table 
        columns={columns} 
        dataSource={resources} 
        rowKey="id" 
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  )
}