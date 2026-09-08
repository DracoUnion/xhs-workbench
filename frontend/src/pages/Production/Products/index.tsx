import { useQuery } from '@tanstack/react-query'
import { Button, Card, Table, Tag, Typography, message } from 'antd'
import { Link } from 'react-router-dom'
import { listProducts } from '../../../api/discovery'
import { promoteProduct } from '../../../api/production'
import { ApiClientError, errorMessage } from '../../../api/http'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

export default function ProductionProducts() {
  const q = useQuery({ queryKey: ['production-products'], queryFn: () => listProducts(undefined, 1, 50) })
  const [msg, msgCtx] = message.useMessage()
  const qc = undefined // eslint-disable-line

  const promote = async (id: number) => {
    try {
      await promoteProduct(id)
      msg.success('已转自产')
    } catch (err) {
      msg.info((err instanceof ApiClientError && err.code) ? '产品接口待接入' : errorMessage(err))
    }
  }

  return (
    <>
      {msgCtx}
      <PageHeader title="产品制作" subtitle="候选商品转自产 · 资料与验收" />
      <Card title="产品列表" loading={q.isLoading}>
        {q.isError ? (
          <EmptyIntegration description="产品接口待接入" onRefresh={() => q.refetch()} />
        ) : (
          <Table
            rowKey="id"
            dataSource={q.data?.data ?? []}
            pagination={false}
            size="small"
            columns={[
              { title: 'ID', dataIndex: 'id', width: 70 },
              { title: '标题', dataIndex: 'title', render: (v, r) => <Link to={`/production/products/${r.id}`}>{v ?? '-'}</Link> },
              { title: '角色', dataIndex: 'role', width: 100, render: (v) => <Tag color={v === 'self-made' ? 'gold' : 'default'}>{v}</Tag> },
              { title: '状态', dataIndex: 'status', width: 110 },
              {
                title: '操作',
                key: 'ops',
                width: 120,
                render: (_, r) => (
                  r.role !== 'self-made' ? <Button size="small" type="link" onClick={() => promote(r.id)}>转自产</Button> : <Typography.Text type="secondary">已自产</Typography.Text>
                ),
              },
            ]}
          />
        )}
      </Card>
    </>
  )
}