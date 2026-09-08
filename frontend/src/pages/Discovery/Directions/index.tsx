import { useQuery } from '@tanstack/react-query'
import { Card, Col, Row, Skeleton, Tag, Typography } from 'antd'
import { ExclamationCircleOutlined } from '@ant-design/icons'
import { listDirections } from '../../../api/discovery'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

const STATUS_COLOR: Record<string, string> = {
  观察中: 'default',
  升温: 'processing',
  已验证: 'success',
  降温: 'warning',
  放弃: 'default',
}

export default function Directions() {
  const q = useQuery({ queryKey: ['directions'], queryFn: listDirections })

  return (
    <>
      <PageHeader title="方向看板" subtitle="品类×形态聚合的已验证方向" />
      {q.isLoading ? (
        <Skeleton active />
      ) : q.isError ? (
        <EmptyIntegration description="方向接口待接入" onRefresh={() => q.refetch()} />
      ) : !q.data?.length ? (
        <EmptyIntegration description="暂无方向数据" onRefresh={() => q.refetch()} />
      ) : (
        <Row gutter={[16, 16]}>
          {q.data.map((d) => (
            <Col key={d.id} xs={24} sm={12} lg={8} xl={6}>
              <Card
                size="small"
                title={d.name}
                extra={<Tag color={STATUS_COLOR[d.status] ?? 'default'}>{d.status}</Tag>}
              >
                <Typography.Paragraph type="secondary" ellipsis={{ rows: 2 }}>
                  {d.evidence ?? '暂无佐证说明'}
                </Typography.Paragraph>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  <ExclamationCircleOutlined /> 支撑账号与销量见后端方向接口（待接入）
                </Typography.Text>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </>
  )
}