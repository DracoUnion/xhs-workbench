import { useQuery } from '@tanstack/react-query'
import { Alert, Card, Col, Empty, List, Row, Skeleton, Statistic, Tag, Typography } from 'antd'
import ReactECharts from 'echarts-for-react'
import { getDashboardSummary } from '../../api/dashboard'
import { errorMessage } from '../../api/http'
import { EmptyIntegration } from '../../components/EmptyIntegration'
import { PageHeader } from '../../components/PageHeader'
import { RunStatusTag } from '../../components/RunStatusTag'

export default function Dashboard() {
  const summary = useQuery({ queryKey: ['dashboard', 'summary'], queryFn: getDashboardSummary })

  if (summary.isLoading) {
    return <><PageHeader title="工作台" subtitle="数据驱动的小红书虚拟产品运营" /><Skeleton active /></>
  }

  if (summary.isError || !summary.data) {
    return (
      <>
        <PageHeader title="工作台" subtitle="数据驱动的小红书虚拟产品运营" />
        <Alert type="info" showIcon message="看板数据暂不可用" description={errorMessage(summary.error)} style={{ marginBottom: 16 }} />
        <EmptyIntegration description="看板汇总接口尚未接入，后端完成后这里会显示实时经营数据。" onRefresh={() => summary.refetch()} />
      </>
    )
  }

  const data = summary.data
  const statusCount = data.directions.reduce<Record<string, number>>((acc, item) => {
    acc[item.status] = (acc[item.status] ?? 0) + 1
    return acc
  }, {})
  const option = {
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: ['48%', '72%'], data: Object.entries(statusCount).map(([name, value]) => ({ name, value })) }],
  }

  return (
    <>
      <PageHeader title="工作台" subtitle={`运营概览 · ${data.date}`} />
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="今日分析账号" value={data.accounts_today} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="今日采集商品" value={data.products_today} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="升温方向" value={data.market?.accelerating ?? 0} valueStyle={{ color: '#cf1322' }} /></Card></Col>
        <Col xs={24} sm={12} lg={6}><Card><Statistic title="降温方向" value={data.market?.cooling ?? 0} valueStyle={{ color: '#8c8c8c' }} /></Card></Col>
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={10}>
          <Card title="方向状态分布">
            {Object.keys(statusCount).length ? <ReactECharts option={option} style={{ height: 260 }} /> : <Empty description="暂无方向数据" />}
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title="产品方向" extra={<Typography.Link href="/discovery/directions">查看全部</Typography.Link>}>
            <List
              dataSource={data.directions}
              locale={{ emptyText: '暂无方向' }}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta title={item.name} description={item.suggestion ?? '暂无建议'} />
                  <div style={{ textAlign: 'right' }}><Tag>{item.status}</Tag><br /><Typography.Text type="secondary">{item.accounts} 个支撑账号</Typography.Text></div>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
      <Card title="近期任务" style={{ marginTop: 16 }}>
        <List
          dataSource={data.recent_runs}
          locale={{ emptyText: '暂无任务' }}
          renderItem={(run) => <List.Item><List.Item.Meta title={run.agent_key} description={`任务 #${run.id}`} /><RunStatusTag status={run.status} /></List.Item>}
        />
      </Card>
    </>
  )
}