import { Layout, Menu, Avatar, Dropdown, Space } from 'antd'
import { UserOutlined, LogoutOutlined, DashboardOutlined, FileOutlined, ClusterOutlined, CloudServerOutlined, TeamOutlined } from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const { Header: AntHeader } = Layout

export default function Header() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
    { key: '/tasks', icon: <ClusterOutlined />, label: '评测任务' },
    { key: '/assets', icon: <FileOutlined />, label: '资产管理' },
    { key: '/resources', icon: <CloudServerOutlined />, label: '算力资源' },
    { key: '/community', icon: <TeamOutlined />, label: '社区' },
  ]

  const userMenu = {
    items: [
      { key: 'profile', icon: <UserOutlined />, label: user?.username },
      { type: 'divider' as const },
      { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: logout },
    ],
  }

  return (
    <AntHeader style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#001529', padding: '0 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <div style={{ color: '#fff', fontSize: '20px', fontWeight: 'bold', marginRight: '40px' }}>
          AI Validation Platform
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1, minWidth: 0 }}
        />
      </div>
      <Dropdown menu={userMenu} placement="bottomRight">
        <Space style={{ cursor: 'pointer' }}>
          <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
          <span style={{ color: '#fff' }}>{user?.username}</span>
        </Space>
      </Dropdown>
    </AntHeader>
  )
}