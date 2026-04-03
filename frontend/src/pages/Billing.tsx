import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Button, Table, Tag, Modal, Form, InputNumber, message, Tabs, Progress } from 'antd'
import { WalletOutlined, CreditCardOutlined, FileTextOutlined, DollarOutlined, WarningOutlined } from '@ant-design/icons'
import { billingApi } from '../services/api'

const { TabPane } = Tabs

export default function Billing() {
  const [balance, setBalance] = useState({ balance: 0, subscription_type: 'free' })
  const [orders, setOrders] = useState<any[]>([])
  const [prices, setPrices] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [rechargeModalVisible, setRechargeModalVisible] = useState(false)
  const [rechargeForm] = Form.useForm()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [balanceRes, ordersRes, pricesRes] = await Promise.all([
        billingApi.getBalance(),
        billingApi.getOrders({ page: 1, page_size: 10 }),
        billingApi.getPrices(),
      ])
      setBalance(balanceRes.data)
      setOrders(ordersRes.data.items || ordersRes.data)
      setPrices(pricesRes.data)
    } catch (error) {
      console.error('Failed to load billing data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRecharge = async (values: { amount: number; payment_method: string }) => {
    try {
      await billingApi.recharge(values)
      message.success('充值成功')
      setRechargeModalVisible(false)
      rechargeForm.resetFields()
      loadData()
    } catch (error) {
      message.error('充值失败')
    }
  }

  const formatMoney = (cents: number) => (cents / 100).toFixed(2)

  const orderColumns = [
    { title: '订单号', dataIndex: 'order_no', key: 'order_no' },
    { 
      title: '金额', 
      dataIndex: 'amount', 
      key: 'amount',
      render: (amount: number) => `¥${formatMoney(amount)}`
    },
    { 
      title: '类型', 
      dataIndex: 'order_type', 
      key: 'order_type',
      render: (type: string) => {
        const map: Record<string, string> = { recharge: '充值', evaluation: '评测', storage: '存储' }
        return <Tag>{map[type] || type}</Tag>
      }
    },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          pending: 'orange', paid: 'green', cancelled: 'red', refunded: 'default'
        }
        const textMap: Record<string, string> = {
          pending: '待支付', paid: '已支付', cancelled: '已取消', refunded: '已退款'
        }
        return <Tag color={colorMap[status]}>{textMap[status] || status}</Tag>
      }
    },
    { 
      title: '时间', 
      dataIndex: 'created_at', 
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString('zh-CN')
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, marginBottom: 24 }}>计费中心</h1>

      {/* 余额卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card>
            <Statistic
              title="账户余额"
              value={formatMoney(balance.balance)}
              prefix={<WalletOutlined />}
              suffix="元"
              valueStyle={{ color: '#52c41a', fontSize: 36 }}
            />
            <div style={{ marginTop: 16 }}>
              <Tag color={balance.subscription_type === 'free' ? 'default' : 'blue'}>
                {balance.subscription_type === 'free' ? '免费版' : 
                 balance.subscription_type === 'basic' ? '基础版' : '专业版'}
              </Tag>
              {balance.balance < 10000 && (
                <Tag color="warning" style={{ marginLeft: 8 }}>
                  <WarningOutlined /> 余额不足
                </Tag>
              )}
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="快速充值">
            <Row gutter={[8, 8]}>
              {[100, 500, 1000, 5000].map((amount) => (
                <Col span={12} key={amount}>
                  <Button 
                    size="large" 
                    block 
                    onClick={() => {
                      rechargeForm.setFieldValue('amount', amount)
                      setRechargeModalVisible(true)
                    }}
                  >
                    ¥{amount}
                  </Button>
                </Col>
              ))}
            </Row>
            <Button 
              type="primary" 
              icon={<DollarOutlined />} 
              block 
              style={{ marginTop: 16 }}
              onClick={() => setRechargeModalVisible(true)}
            >
              自定义充值
            </Button>
          </Card>
        </Col>
      </Row>

      {/* 价格表 */}
      <Card title="价格说明" style={{ marginBottom: 24 }}>
        <Tabs defaultActiveKey="evaluation">
          <TabPane tab="评测价格" key="evaluation">
            <Table
              dataSource={Object.entries(prices.evaluation_types || {}).map(([key, val]: any) => ({ 
                key, ...val, type: key 
              }))}
              columns={[
                { title: '评测类型', dataIndex: 'name', key: 'name' },
                { title: '单价', dataIndex: 'base_price', key: 'base_price', render: (p: number) => `¥${p}/时/GPU` },
                { title: '单位', dataIndex: 'unit', key: 'unit' },
              ]}
              pagination={false}
              size="small"
            />
          </TabPane>
          <TabPane tab="算力资源" key="resources">
            <Table
              dataSource={Object.entries(prices.resources || {}).map(([key, val]: any) => ({ 
                key, ...val, model: key 
              }))}
              columns={[
                { title: '型号', dataIndex: 'model', key: 'model' },
                { title: '单价', dataIndex: 'price', key: 'price', render: (p: number) => `¥${p}/时` },
              ]}
              pagination={false}
              size="small"
            />
          </TabPane>
          <TabPane tab="存储价格" key="storage">
            <p>存储: ¥{prices.storage?.price || '0.5'}/GB/月</p>
            <p>带宽: ¥{prices.bandwidth?.price || '0.8'}/GB</p>
          </TabPane>
        </Tabs>
      </Card>

      {/* 订单列表 */}
      <Card title="订单记录" extra={<Button icon={<FileTextOutlined />}>发票管理</Button>}>
        <Table
          dataSource={orders}
          columns={orderColumns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* 充值弹窗 */}
      <Modal
        title="充值"
        open={rechargeModalVisible}
        onCancel={() => setRechargeModalVisible(false)}
        footer={null}
      >
        <Form form={rechargeForm} layout="vertical" onFinish={handleRecharge}>
          <Form.Item name="amount" label="充值金额" rules={[{ required: true, message: '请输入充值金额' }]}>
            <InputNumber min={1} max={100000} style={{ width: '100%' }} placeholder="请输入金额" />
          </Form.Item>
          <Form.Item name="payment_method" label="支付方式" initialValue="alipay">
            <Radio.Group>
              <Radio.Button value="alipay">支付宝</Radio.Button>
              <Radio.Button value="wechat">微信</Radio.Button>
              <Radio.Button value="bank">银行转账</Radio.Button>
            </Radio.Group>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              确认充值
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

import { Radio } from 'antd'