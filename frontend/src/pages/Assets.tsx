import { useEffect, useState } from 'react'
import { Table, Button, Tag, Space, Modal, Form, Input, Select, message, Card, Row, Col } from 'antd'
import { PlusOutlined, DownloadOutlined } from '@ant-design/icons'
import { assetApi } from '../services/api'

const { Option } = Select

const typeMap: Record<string, { color: string; text: string }> = {
  dataset: { color: 'blue', text: '数据集' },
  model: { color: 'green', text: '模型' },
  framework: { color: 'purple', text: '框架' },
  tool: { color: 'orange', text: '工具' },
  report: { color: 'cyan', text: '报告' },
  image: { color: 'magenta', text: '镜像' },
}

export default function Assets() {
  const [assets, setAssets] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadAssets()
  }, [])

  const loadAssets = async () => {
    setLoading(true)
    try {
      const response = await assetApi.list()
      setAssets(response.data)
    } catch (error) {
      message.error('加载资产失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (values: any) => {
    try {
      await assetApi.create(values)
      message.success('创建成功')
      setModalVisible(false)
      form.resetFields()
      loadAssets()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const formatSize = (bytes: number) => {
    if (!bytes) return '-'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
  }

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { 
      title: '类型', 
      dataIndex: 'asset_type', 
      key: 'asset_type',
      render: (type: string) => <Tag color={typeMap[type]?.color}>{typeMap[type]?.text}</Tag>
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { 
      title: '大小', 
      dataIndex: 'file_size', 
      key: 'file_size',
      render: (size: number) => formatSize(size)
    },
    { 
      title: '公开', 
      dataIndex: 'is_public', 
      key: 'is_public',
      render: (isPublic: boolean) => isPublic ? <Tag color="green">是</Tag> : <Tag>否</Tag>
    },
    { 
      title: '免费', 
      dataIndex: 'is_free', 
      key: 'is_free',
      render: (isFree: boolean) => isFree ? <Tag color="blue">是</Tag> : <Tag>否</Tag>
    },
    { 
      title: '下载次数', 
      dataIndex: 'download_count', 
      key: 'download_count' 
    },
    { 
      title: '创建时间', 
      dataIndex: 'created_at', 
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString('zh-CN')
    },
  ]

  const stats = {
    total: assets.length,
    datasets: assets.filter(a => a.asset_type === 'dataset').length,
    models: assets.filter(a => a.asset_type === 'model').length,
    tools: assets.filter(a => a.asset_type === 'tool').length,
  }

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 style={{ fontSize: 24 }}>资产管理</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
          添加资产
        </Button>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Card.Meta title="总资产" description={stats.total} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Card.Meta title="数据集" description={stats.datasets} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Card.Meta title="模型" description={stats.models} />
          </Card>
        </Col>
      </Row>

      <Table 
        columns={columns} 
        dataSource={assets} 
        rowKey="id" 
        loading={loading}
      />

      <Modal
        title="添加资产"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="asset_type" label="资产类型" rules={[{ required: true }]}>
            <Select>
              <Option value="dataset">数据集</Option>
              <Option value="model">模型</Option>
              <Option value="framework">框架</Option>
              <Option value="tool">工具</Option>
              <Option value="report">报告</Option>
              <Option value="image">镜像</Option>
            </Select>
          </Form.Item>
          <Form.Item name="is_public" label="公开" valuePropName="checked" initialValue={false}>
            <Input type="checkbox" />
          </Form.Item>
          <Form.Item name="is_free" label="免费" valuePropName="checked" initialValue={false}>
            <Input type="checkbox" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">创建</Button>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}