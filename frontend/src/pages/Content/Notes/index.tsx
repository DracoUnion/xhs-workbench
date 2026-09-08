import { useQuery } from '@tanstack/react-query'
import { Card, Table, Tag, Typography } from 'antd'
import { Link } from 'react-router-dom'
import { listNotes } from '../../../api/content'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

export default function Notes() {
  const q = useQuery({ queryKey: ['notes'], queryFn: () => listNotes(undefined, 1, 50) })

  return (
    <>
      <PageHeader title="对标笔记库" subtitle="图文/视频对标 + 去重 + 拆解状态" />
      <Card loading={q.isLoading}>
        {q.isError ? <EmptyIntegration description="对标笔记接口待接入" onRefresh={() => q.refetch()} /> : (
          <Table
            rowKey="id"
            dataSource={q.data?.data ?? []}
            pagination={false}
            size="small"
            columns={[
              { title: 'ID', dataIndex: 'id', width: 70 },
              { title: '标题', dataIndex: 'title', render: (v, r) => <Link to={`/content/notes/${r.id}`}>{v ?? '-'}</Link> },
              { title: '作者', dataIndex: 'author', width: 120 },
              { title: '类型', dataIndex: 'media_type', width: 80, render: (v) => <Tag color={v === 'video' ? 'blue' : 'green'}>{v}</Tag> },
              { title: '拆解', dataIndex: 'analyzed', width: 80, render: (v: boolean) => (v ? <Tag color="success">已拆解</Tag> : <Tag>未拆解</Tag>) },
            ]}
          />
        )}
      </Card>
    </>
  )
}