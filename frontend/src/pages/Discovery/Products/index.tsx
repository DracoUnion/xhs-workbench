import { useQuery } from '@tanstack/react-query'
import { Card, Table, Typography } from 'antd'
import { Link } from 'react-router-dom'
import { listProducts } from '../../../api/discovery'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

export default function Products() {
  const q = useQuery({ queryKey: ['products'], queryFn: () => listProducts(undefined, 1, 50) })

  return (
    <>
      <PageHeader title="商品库" subtitle="采集到的商品与校验状态" />
      <Card loading={q.isLoading}>
        {q.isError ? (
          <EmptyIntegration description="商品接口待接入" onRefresh={() => q.refetch()} />
        ) : (
          <Table
            rowKey="id"
            dataSource={q.data?.data ?? []}
            pagination={false}
            size="small"
            columns={[
              { title: 'ID', dataIndex: 'id', width: 70 },
              { title: '标题', dataIndex: 'title', render: (v, r) => <Link to={`/discovery/products/${r.id}`}>{v ?? '-'}</Link> },
              { title: '价格(分)', dataIndex: 'price_cents', width: 100 },
              { title: '销量', dataIndex: 'sales', width: 90 },
              { title: '形态', dataIndex: 'form', width: 90 },
              { title: '状态', dataIndex: 'status', width: 110, render: (v) => <Typography.Text type="secondary">{v}</Typography.Text> },
            ]}
          />
        )}
      </Card>
    </>
  )
}