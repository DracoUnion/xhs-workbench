import { useQuery } from '@tanstack/react-query'
import { Card, Table, Typography } from 'antd'
import { Link } from 'react-router-dom'
import { listAccounts } from '../../../api/discovery'
import { errorMessage } from '../../../api/http'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

export default function Accounts() {
  const q = useQuery({ queryKey: ['accounts'], queryFn: () => listAccounts(1, 50) })

  return (
    <>
      <PageHeader title="账号画像" subtitle="按评分排序的候选账号" />
      <Card loading={q.isLoading}>
        {q.isError ? (
          <EmptyIntegration description="账号接口待接入" onRefresh={() => q.refetch()} />
        ) : (
          <Table
            rowKey="id"
            dataSource={q.data?.data ?? []}
            pagination={false}
            size="small"
            columns={[
              { title: 'ID', dataIndex: 'id', width: 70 },
              { title: '昵称', dataIndex: 'nickname', render: (v, r) => <Link to={`/discovery/accounts/${r.id}`}>{v ?? r.xhs_user_id}</Link> },
              { title: '粉丝数', dataIndex: 'fans', width: 120 },
              { title: '总分', dataIndex: 'score', width: 120, render: (v) => <Typography.Text strong>{v ?? '-'}</Typography.Text> },
            ]}
          />
        )}
      </Card>
    </>
  )
}