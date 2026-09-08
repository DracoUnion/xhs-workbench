import { useQuery } from '@tanstack/react-query'
import { Card, Descriptions, Skeleton, Typography } from 'antd'
import { useParams } from 'react-router-dom'
import { getAccount } from '../../../api/discovery'
import { errorMessage } from '../../../api/http'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

export default function AccountDetail() {
  const { id } = useParams()
  const accountId = Number(id)
  const q = useQuery({ queryKey: ['account', accountId], queryFn: () => getAccount(accountId), enabled: !!accountId })

  return (
    <>
      <PageHeader title={`账号 #${id}`} subtitle="评分明细与商品入口" />
      <Card loading={q.isLoading}>
        {q.isError ? (
          <EmptyIntegration description="账号接口待接入" onRefresh={() => q.refetch()} />
        ) : (
          <>
            <Descriptions column={2} size="small">
              <Descriptions.Item label="昵称">{q.data?.nickname ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="粉丝数">{q.data?.fans ?? '-'}</Descriptions.Item>
              <Descriptions.Item label="总分"><Typography.Text strong>{q.data?.score ?? '-'}</Typography.Text></Descriptions.Item>
              <Descriptions.Item label="上榜天数">{q.data?.board_days ?? 0}</Descriptions.Item>
            </Descriptions>
            <Typography.Paragraph type="secondary" style={{ marginTop: 16 }}>
              评分明细（需求证据 / 可信度 / 低粉加成）与商品列表：账号分析接口接入后展示。
            </Typography.Paragraph>
          </>
        )}
      </Card>
    </>
  )
}