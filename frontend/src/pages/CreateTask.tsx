import { useEffect, useState } from 'react'
import { Card, Row, Col, Tag, Button, Modal, Form, Select, Input, Tabs, Empty, Spin, Descriptions, Progress, Badge, Divider } from 'antd'
import { ThunderboltOutlined, ExperimentOutlined, CheckCircleOutlined, ClockCircleOutlined, FileTextOutlined, StarOutlined } from '@ant-design/icons'
import { taskApi, templateApi } from '../services/api'

const { Option } = Select
const { TextArea } = Input

const typeMap: Record<string, { color: string; text: string }> = {
  chip: { color: 'red', text: '芯片' },
  operator: { color: 'orange', text: '算子' },
  framework: { color: 'blue', text: '框架' },
  model: { color: 'green', text: '模型' },
  scenario: { color: 'purple', text: '场景' },
}

const evaluationTypeMap: Record<string, { color: string; text: string }> = {
  performance: { color: 'blue', text: '性能评测' },
  precision: { color: 'green', text: '精度评测' },
  compatibility: { color: 'purple', text: '兼容性评测' },
  stability: { color: 'orange', text: '稳定性评测' },
}

export default function CreateTask() {
  const [templates, setTemplates] = useState<any[]>([])
  const [categories, setCategories] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null)
  const [activeCategory, setActiveCategory] = useState('all')
  const [form] = Form.useForm()

  useEffect(() => {
    loadTemplates()
  }, [activeCategory])

  const loadTemplates = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (activeCategory !== 'all') {
        params.category = activeCategory
      }
      
      const [templatesRes, categoriesRes] = await Promise.all([
        templateApi.list(params),
        templateApi.getCategories(),
      ])
      
      setTemplates(templatesRes.data)
      setCategories(categoriesRes.data)
    } catch (error) {
      console.error('Failed to load templates:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectTemplate = (template: any) => {
    setSelectedTemplate(template)
    form.setFieldsValue({
      name: `${template.name}`,
      description: template.description,
      evaluation_type: template.evaluation_type,
      evaluation_target: template.evaluation_target,
    })
    setModalVisible(true)
  }

  const handleSubmit = async (values: any) => {
    try {
      await taskApi.create({
        ...values,
        config: selectedTemplate?.default_config,
        priority: 'medium',
        required_gpu_count: 1,
        required_memory_gb: 16,
      })
      setModalVisible(false)
      form.resetFields()
      setSelectedTemplate(null)
    } catch (error) {
      console.error('Failed to create task:', error)
    }
  }

  const tabItems = [
    { key: 'all', label: '全部' },
    ...categories.map(cat => ({ key: cat.id, label: cat.name })),
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24 }}>创建评测任务</h1>
        <p style={{ color: '#666' }}>选择评测模板或自定义配置</p>
      </div>

      <Tabs 
        activeKey={activeCategory} 
        onChange={setActiveCategory}
        items={tabItems}
        style={{ marginBottom: 24 }}
      />

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
        </div>
      ) : templates.length === 0 ? (
        <Empty description="暂无模板" />
      ) : (
        <Row gutter={[16, 16]}>
          {templates.map((template) => (
            <Col xs={24} lg={12} xl={8} key={template.id}>
              <Card
                hoverable
                onClick={() => handleSelectTemplate(template)}
                actions={[
                  <Button type="link" icon={<ThunderboltOutlined />}>创建任务</Button>,
                ]}
              >
                <Card.Meta
                  title={
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>{template.name}</span>
                      {template.is_free ? (
                        <Tag color="green">免费</Tag>
                      ) : (
                        <Tag color="orange">收费</Tag>
                      )}
                    </div>
                  }
                  description={
                    <div>
                      <p style={{ color: '#666', marginBottom: 8 }}>{template.description}</p>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                        <Tag color={evaluationTypeMap[template.evaluation_type]?.color}>
                          {evaluationTypeMap[template.evaluation_type]?.text}
                        </Tag>
                        <Tag color={typeMap[template.evaluation_target]?.color}>
                          {typeMap[template.evaluation_target]?.text}
                        </Tag>
                      </div>
                      <div style={{ color: '#999', fontSize: 12 }}>
                        <ClockCircleOutlined /> 预计时长: {template.estimated_time_hours}小时
                      </div>
                    </div>
                  }
                />
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {/* 创建任务弹窗 */}
      <Modal
        title="创建评测任务"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        width={700}
        footer={null}
      >
        {selectedTemplate && (
          <Form form={form} layout="vertical" onFinish={handleSubmit}>
            <Form.Item name="name" label="任务名称" rules={[{ required: true }]}>
              <Input placeholder="请输入任务名称" />
            </Form.Item>

            <Form.Item name="description" label="描述">
              <TextArea rows={2} placeholder="任务描述（可选）" />
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="evaluation_type" label="评测类型" rules={[{ required: true }]}>
                  <Select placeholder="选择评测类型">
                    <Option value="performance">性能评测</Option>
                    <Option value="precision">精度评测</Option>
                    <Option value="compatibility">兼容性评测</Option>
                    <Option value="stability">稳定性评测</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="evaluation_target" label="评测对象" rules={[{ required: true }]}>
                  <Select placeholder="选择评测对象">
                    <Option value="chip">芯片</Option>
                    <Option value="operator">算子</Option>
                    <Option value="framework">框架</Option>
                    <Option value="model">模型</Option>
                    <Option value="scenario">场景</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="required_gpu_count" label="GPU数量" initialValue={1}>
                  <Select>
                    <Option value={1}>1 GPU</Option>
                    <Option value={2}>2 GPU</Option>
                    <Option value={4}>4 GPU</Option>
                    <Option value={8}>8 GPU</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="priority" label="优先级" initialValue="medium">
                  <Select>
                    <Option value="low">低</Option>
                    <Option value="medium">中</Option>
                    <Option value="high">高</Option>
                    <Option value="urgent">紧急</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            {/* 模板默认配置 */}
            {selectedTemplate?.default_config && (
              <Card size="small" title="模板默认配置" style={{ marginBottom: 16 }}>
                <Descriptions column={2} size="small">
                  {Object.entries(selectedTemplate.default_config).map(([key, value]) => (
                    <Descriptions.Item key={key} label={key}>
                      {Array.isArray(value) ? value.join(', ') : String(value)}
                    </Descriptions.Item>
                  ))}
                </Descriptions>
              </Card>
            )}

            <Form.Item>
              <Button type="primary" htmlType="submit" block>
                创建任务
              </Button>
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  )
}