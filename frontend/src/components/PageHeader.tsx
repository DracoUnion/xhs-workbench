import type { ReactNode } from 'react'
import { Space, Typography } from 'antd'

interface PageHeaderProps {
  title: string
  subtitle?: string
  extra?: ReactNode
}

export function PageHeader({ title, subtitle, extra }: PageHeaderProps) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
      <div>
        <Typography.Title level={4} style={{ margin: 0 }}>
          {title}
        </Typography.Title>
        {subtitle && <Typography.Text type="secondary">{subtitle}</Typography.Text>}
      </div>
      {extra && <Space>{extra}</Space>}
    </div>
  )
}