import { Suspense } from 'react'
import { Avatar, Badge, Button, Dropdown, Layout, Menu, Space, Spin, theme, Typography } from 'antd'
import {
  DashboardOutlined,
  FireOutlined,
  FileTextOutlined,
  ToolOutlined,
  OrderedListOutlined,
  RobotOutlined,
  SettingOutlined,
  RocketOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/auth'
import { useTaskStore } from '../stores/tasks'
import { useTaskWebSocket } from '../hooks/useTaskWebSocket'

const { Sider, Header, Content } = Layout

const MENU_GROUPS = [
  { group: '总览', icon: <DashboardOutlined />, key: '/', label: '工作台' },
  {
    group: '需求发现',
    icon: <FireOutlined />,
    items: [
      { key: '/discovery/rankings', label: '榜单采集' },
      { key: '/discovery/accounts', label: '账号画像' },
      { key: '/discovery/products', label: '商品库' },
      { key: '/discovery/directions', label: '方向看板' },
    ],
  },
  {
    group: '产品制作',
    icon: <ToolOutlined />,
    items: [
      { key: '/production/products', label: '产品列表' },
    ],
  },
  {
    group: '内容获客',
    icon: <FileTextOutlined />,
    items: [
      { key: '/content/keywords', label: '关键词' },
      { key: '/content/notes', label: '对标笔记库' },
      { key: '/content/templates', label: '模板聚类' },
      { key: '/content/skills', label: 'Skill' },
      { key: '/content/contents', label: '内容包' },
    ],
  },
  { group: '任务中心', icon: <OrderedListOutlined />, key: '/tasks', label: '任务中心' },
  { group: '小红书', icon: <RocketOutlined />, key: '/xhs', label: '小红书登录态' },
  { group: '设置', icon: <SettingOutlined />, key: '/settings', label: '设置' },
]

function buildMenuItems() {
  return MENU_GROUPS.map((g) =>
    'items' in g
      ? {
          key: g.group,
          icon: g.icon,
          label: g.group,
          children: g.items!.map((it) => ({ key: it.key, label: it.label })),
        }
      : { key: g.key!, icon: g.icon, label: g.label },
  )
}

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const connected = useTaskStore((s) => s.connected)
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  // 挂载 WS 实时通道（受保护页全程可用）
  useTaskWebSocket()

  const FLAT_ROUTES = MENU_GROUPS.flatMap((g) =>
    'items' in g && g.items ? g.items.map((it) => it.key) : g.key ? [g.key] : [],
  )
  const selected =
    FLAT_ROUTES.slice()
      .sort((a, b) => b.length - a.length)
      .find((k) => location.pathname.startsWith(k)) ?? '/'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible breakpoint="lg" width={224} theme="dark">
        <div
          style={{
            height: 56,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 700,
            fontSize: 15,
            letterSpacing: 0.5,
          }}
        >
          小红书 AI 工作台
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selected]}
          defaultOpenKeys={MENU_GROUPS.filter((g) => 'items' in g).map((g) => g.group)}
          items={buildMenuItems()}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: colorBgContainer,
            padding: '0 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
          }}
        >
          <Space size="middle">
            <Badge status={connected ? 'processing' : 'default'} text={connected ? '实时连接中' : '未连接'} />
          </Space>
          <Dropdown
            menu={{
              items: [
                { key: 'logout', icon: <LogoutOutlined />, label: '退出登录' },
              ],
              onClick: ({ key }) => {
                if (key === 'logout') {
                  logout()
                  navigate('/login')
                }
              },
            }}
          >
            <Space style={{ cursor: 'pointer' }}>
              <Avatar size="small" icon={<UserOutlined />} />
              <Typography.Text>{user?.username ?? 'admin'}</Typography.Text>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: 16 }}>
          <div
            style={{
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
              padding: 24,
              minHeight: 'calc(100vh - 128px)',
            }}
          >
            <Suspense
              fallback={
                <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 80 }}>
                  <Spin size="large" />
                </div>
              }
            >
              <Outlet />
            </Suspense>
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}