import { useQuery } from '@tanstack/react-query'
import { Button, Card, List, Tag, Typography } from 'antd'
import { Link } from 'react-router-dom'
import { listSkills } from '../../../api/content'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

export default function Skills() {
  const q = useQuery({ queryKey: ['skills'], queryFn: () => listSkills(undefined) })
  return (
    <>
      <PageHeader title="内容 Skill" subtitle="产品事实白名单 + 文案/图片规范" />
      <Card loading={q.isLoading}>
        {q.isError ? <EmptyIntegration description="Skill 接口待接入" onRefresh={() => q.refetch()} /> : (
          <List
            dataSource={q.data ?? []}
            locale={{ emptyText: '暂无 Skill' }}
            renderItem={(s) => (
              <List.Item actions={[<Link key="edit" to={`/content/skills/${s.id}`}><Button type="link" size="small">编辑</Button></Link>]}>
                <List.Item.Meta title={s.name} description={`产品 #${s.product_id} · 当前版本 v${s.current_version}`} />
                <Typography.Text><Tag color={s.status === 'active' ? 'success' : 'default'}>{s.status}</Tag><Tag>{s.review_policy}</Tag></Typography.Text>
              </List.Item>
            )}
          />
        )}
      </Card>
    </>
  )
}