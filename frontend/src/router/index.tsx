import { lazy, Suspense, type ReactNode } from 'react'
import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom'
import { Spin } from 'antd'
import { useAuthStore } from '../stores/auth'
import MainLayout from '../layouts/MainLayout'

const Login = lazy(() => import('../pages/Login'))
const Dashboard = lazy(() => import('../pages/Dashboard'))
const TaskCenter = lazy(() => import('../pages/TaskCenter'))
const XhsPage = lazy(() => import('../pages/Xhs'))
const Settings = lazy(() => import('../pages/Settings'))
const NotFound = lazy(() => import('../pages/NotFound'))

// 需求发现
const Rankings = lazy(() => import('../pages/Discovery/Rankings'))
const Accounts = lazy(() => import('../pages/Discovery/Accounts'))
const AccountDetail = lazy(() => import('../pages/Discovery/AccountDetail'))
const Products = lazy(() => import('../pages/Discovery/Products'))
const ProductDetail = lazy(() => import('../pages/Discovery/ProductDetail'))
const Directions = lazy(() => import('../pages/Discovery/Directions'))
// 产品制作
const ProductionProducts = lazy(() => import('../pages/Production/Products'))
const ProductStudio = lazy(() => import('../pages/Production/ProductStudio'))
// 内容获客
const Keywords = lazy(() => import('../pages/Content/Keywords'))
const Notes = lazy(() => import('../pages/Content/Notes'))
const NoteDetail = lazy(() => import('../pages/Content/NoteDetail'))
const Templates = lazy(() => import('../pages/Content/Templates'))
const Skills = lazy(() => import('../pages/Content/Skills'))
const SkillEditor = lazy(() => import('../pages/Content/SkillEditor'))
const Contents = lazy(() => import('../pages/Content/Contents'))

function Protected() {
  const token = useAuthStore((s) => s.accessToken)
  if (!token) return <Navigate to="/login" replace />
  return <MainLayout />
}

export const router = createBrowserRouter([
  { path: '/login', element: <Login /> },
  {
    element: <Protected />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/discovery/rankings', element: <Rankings /> },
      { path: '/discovery/accounts', element: <Accounts /> },
      { path: '/discovery/accounts/:id', element: <AccountDetail /> },
      { path: '/discovery/products', element: <Products /> },
      { path: '/discovery/products/:id', element: <ProductDetail /> },
      { path: '/discovery/directions', element: <Directions /> },
      { path: '/production/products', element: <ProductionProducts /> },
      { path: '/production/products/:id', element: <ProductStudio /> },
      { path: '/content/keywords', element: <Keywords /> },
      { path: '/content/notes', element: <Notes /> },
      { path: '/content/notes/:id', element: <NoteDetail /> },
      { path: '/content/templates', element: <Templates /> },
      { path: '/content/skills', element: <Skills /> },
      { path: '/content/skills/:id', element: <SkillEditor /> },
      { path: '/content/contents', element: <Contents /> },
      { path: '/tasks', element: <TaskCenter /> },
      { path: '/xhs', element: <XhsPage /> },
      { path: '/settings', element: <Settings /> },
    ],
  },
  { path: '*', element: <NotFound /> },
])
