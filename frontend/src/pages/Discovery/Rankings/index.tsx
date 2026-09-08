import { Card, Empty, Table, Tag } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'
import { startRankingCollection } from '../../../api/discovery'
import { Button, message } from 'antd'

export default function Rankings() {
  const [msg, ctx] = message.useMessage()
  const collect = useMutation({
    mutationFn: () => startRankingCollection(['read_excellent_content']),
    onSuccess: () => msg.success('采集任务已提交'),
    onError: () => msg.info('榜单采集接口尚未接入'),
  })
  return <>
    {ctx}
    <PageHeader title="榜单采集" subtitle="千帆 8 个榜单入口 · 每页 60~90 秒随机延迟" extra={<Button type="primary" onClick={() => collect.mutate()} loading={collect.isPending}>发起采集</Button>} />
    <Card title="榜单入口">
      <Table rowKey="key" dataSource={[]} pagination={false} columns={[{ title: '入口', dataIndex: 'name' }, { title: '页数', dataIndex: 'page_max' }, { title: '状态', render: () => <Tag>待接入</Tag> }]} locale={{ emptyText: <EmptyIntegration description="榜单数据接口待接入，接入后将在此展示 8 个入口与采集进度。" /> }} />
    </Card>
  </>
}