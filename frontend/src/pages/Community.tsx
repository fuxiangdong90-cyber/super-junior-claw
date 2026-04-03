import { useEffect, useState } from 'react'
import { Card, Row, Col, List, Tag, Button, Input, Tabs, Pagination, Empty, Spin } from 'antd'
import { MessageOutlined, EyeOutlined, LikeOutlined, SearchOutlined, FireOutlined } from '@ant-design/icons'
import { communityApi } from '../services/api'

const { Search } = Input

const typeMap: Record<string, { color: string; text: string }> = {
  dataset: { color: 'blue', text: '数据集' },
  model: { color: 'green', text: '模型' },
  framework: { color: 'purple', text: '框架' },
  tool: { color: 'orange', text: '工具' },
  report: { color: 'cyan', text: '报告' },
}

export default function Community() {
  const [posts, setPosts] = useState<any[]>([])
  const [categories, setCategories] = useState<any[]>([])
  const [tags, setTags] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [activeTab, setActiveTab] = useState('all')

  useEffect(() => {
    loadData()
  }, [page, activeTab])

  const loadData = async () => {
    setLoading(true)
    try {
      const [postsRes, categoriesRes, tagsRes] = await Promise.all([
        communityApi.getPosts({ page, page_size: 10, category: activeTab === 'all' ? undefined : activeTab }),
        communityApi.getCategories(),
        communityApi.getTags(),
      ])
      setPosts(postsRes.data.items || postsRes.data)
      setCategories(categoriesRes.data)
      setTags(tagsRes.data)
      setTotal(postsRes.data.total || postsRes.data.length)
    } catch (error) {
      console.error('Failed to load community data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (value: string) => {
    console.log('Search:', value)
    // 实现搜索
  }

  const tabItems = [
    { key: 'all', label: '全部' },
    { key: 'dataset', label: '数据集' },
    { key: 'model', label: '模型' },
    { key: 'framework', label: '框架' },
    { key: 'tool', label: '工具' },
  ]

  return (
    <div style={{ padding: 24 }}>
      {/* 顶部Banner */}
      <div style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
        borderRadius: 16, 
        padding: '40px 24px',
        marginBottom: 24,
        color: '#fff',
        textAlign: 'center'
      }}>
        <h1 style={{ color: '#fff', fontSize: 32, marginBottom: 8 }}>
          <FireOutlined style={{ marginRight: 12 }} />
          AI验证平台社区
        </h1>
        <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: 16 }}>
          国产AI软硬件评测资源集合地 · 免费资源下载 · 技术交流社区
        </p>
        <Search 
          placeholder="搜索资源、教程、问题..." 
          size="large"
          style={{ maxWidth: 600, marginTop: 24 }}
          onSearch={handleSearch}
          enterButton={<SearchOutlined />}
        />
      </div>

      <Row gutter={24}>
        {/* 左侧内容区 */}
        <Col xs={24} lg={16}>
          <Card>
            <Tabs 
              activeKey={activeTab} 
              onChange={setActiveTab}
              items={tabItems}
            />
            
            {loading ? (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Spin size="large" />
              </div>
            ) : posts.length === 0 ? (
              <Empty description="暂无内容" />
            ) : (
              <List
                dataSource={posts}
                renderItem={(post) => (
                  <List.Item
                    style={{ padding: '16px 0' }}
                    actions={[
                      <span key="view"><EyeOutlined /> {post.view_count || 0}</span>,
                      <span key="like"><LikeOutlined /> {post.like_count || 0}</span>,
                      <span key="comment"><MessageOutlined /> {post.comment_count || 0}</span>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <a href={`/community/post/${post.id}`} style={{ fontSize: 16 }}>
                          {post.title}
                        </a>
                      }
                      description={
                        <div>
                          <Tag color={typeMap[post.category_id]?.color}>
                            {typeMap[post.category_id]?.text || post.category_id}
                          </Tag>
                          {post.tags?.map((tag: string) => (
                            <Tag key={tag} color="default">{tag}</Tag>
                          ))}
                          <span style={{ color: '#999', marginLeft: 8 }}>
                            {new Date(post.created_at).toLocaleDateString('zh-CN')}
                          </span>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
            
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Pagination 
                current={page} 
                total={total} 
                onChange={setPage}
                pageSize={10}
              />
            </div>
          </Card>
        </Col>

        {/* 右侧侧边栏 */}
        <Col xs={24} lg={8}>
          {/* 分类 */}
          <Card title="分类" style={{ marginBottom: 16 }}>
            <List
              size="small"
              dataSource={categories}
              renderItem={(cat) => (
                <List.Item>
                  <a href={`/community?category=${cat.id}`}>{cat.name}</a>
                  <Tag>{cat.post_count}</Tag>
                </List.Item>
              )}
            />
          </Card>

          {/* 热门标签 */}
          <Card title="热门标签" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {tags.map((tag) => (
                <Tag 
                  key={tag.id} 
                  color="blue" 
                  style={{ cursor: 'pointer' }}
                >
                  {tag.name} ({tag.post_count})
                </Tag>
              ))}
            </div>
          </Card>

          {/* 快速入口 */}
          <Card title="快速入口">
            <Row gutter={[8, 8]}>
              <Col span={12}>
                <Button type="primary" block>发布资源</Button>
              </Col>
              <Col span={12}>
                <Button block>发帖交流</Button>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  )
}