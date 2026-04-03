import { useEffect, useState } from 'react'
import { Table, Button, Tag, Space, Modal, Form, Input, Select, InputNumber, message } from 'antd'
import { PlusOutlined, SyncOutlined, StopOutlined, DeleteOutlined } from '@ant-design/icons'
import { taskApi } from '../services/api'

const { Option } = Select
const { TextArea } = Input

const statusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '待执行' },
  queued: { color: 'processing', text: '排队中' },
  running: { color: 'processing', text: '执行中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
  cancelled: { color: 'default', text: '已取消' },
}

export default function Tasks() {
  const [tasks, setTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [modalVisible, setModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadTasks()
  }, [])

  const loadTasks = async () => {
    try {
      const response = await taskApi.list()
      setTasks(response.data)
    } catch (error) {
      message.error('加载任务失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (values: any) => {
    try {
      await taskApi.create(values)
      message.success('创建成功')
      setModalVisible(false)
      form.resetFields()
      loadTasks()
    } catch (error) {
      message.error('创建失败')
    }
  }

  const handleCancel = async (id: string) => {
    try {
      await taskApi.update(id, { status: 'cancelled' })
      message.success('已取消')
      loadTasks()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await taskApi.delete(id)
      message.success('删除成功')
      loadTasks()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const columns = [
    { title: '任务名称', dataIndex: 'name', key: 'name' },
    { 
      title: '类型', 
      dataIndex: 'evaluation_type', 
      key: 'evaluation_type',
      render: (type: string) => <Tag>{type}</Tag>
    },
    { 
      title: '对象', 
      dataIndex: 'evaluation_target', 
      key: 'evaluation_target',
      render: (target: string) => <Tag color="blue">{target}</Tag>
    },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => (
        <Tag color={statusMap[status]?.color}>
          {statusMap[status]?.text}
        </Tag>
      )
    },
    { title: '进度', dataIndex: 'progress', key: 'progress', render: (p: number) => `${p}%` },
    { title: 'GPU数量', dataIndex: 'required_gpu_count', key: 'required_gpu_count' },
    { 
      title: '创建时间', 
      dataIndex: 'created_at', 
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          {record.status === 'running' && (
            <Button size="small" icon={<StopOutlined />} onClick={() => handleCancel(record.id)}>
              取消
            </Button>
          )}
          {['completed', 'failed', 'cancelled'].includes(record.status) && (
            <Button size="small" icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>
              删除
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 style={{ fontSize: 24 }}>评测任务</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
          创建任务
        </Button>
      </div>

      <Table 
        columns={columns} 
        dataSource={tasks} 
        rowKey="id" 
        loading={loading}
      />

      <Modal
        title="创建评测任务"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="任务名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item name="evaluation_type" label="评测类型" rules={[{ required: true }]}>
            <Select>
              <Option value="performance">性能评测</Option>
              <Option value="precision">精度评测</Option>
              <Option value="compatibility">兼容性评测</Option>
              <Option value="stability">稳定性评测</Option>
            </Select>
          </Form.Item>
          <Form.Item name="evaluation_target" label="评测对象" rules={[{ required: true }]}>
            <Select>
              <Option value="chip">芯片</Option>
              <Option value="operator">算子</Option>
              <Option value="framework">框架</Option>
              <Option value="model">模型</Option>
              <Option value="scenario">场景</Option>
            </Select>
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue="medium">
            <Select>
              <Option value="low">低</Option>
              <Option value="medium">中</Option>
              <Option value="high">高</Option>
              <Option value="urgent">紧急</Option>
            </Select>
          </Form.Item>
          <Form.Item name="required_gpu_count" label="GPU数量" initialValue={1}>
            <InputNumber min={1} max={8} />
          </Form.Item>
          <Form.Item name="required_memory_gb" label="内存(GB)" initialValue={16}>
            <InputNumber min={1} max={256} />
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