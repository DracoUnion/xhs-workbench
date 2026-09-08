import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Badge, Button, Card, List, Space, Tag, Typography, message } from 'antd'
import { templateToSkill, listTemplates } from '../../../api/content'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

export default function Templates() {
  const qc = useQueryClient()
  const [msg, msgCtx] = message.useMessage()
  const q = useQuery({ queryKey: ['templates'], queryFn: () => listTemplates(undefined) })

  const toSkill = useMutation({
    mutationFn: (id: number) => templateToSkill(id),
    onSuccess: () => { msg.success('已生成 Skill 草案'); qc.invalidateQueries({ queryKey: ['templates'] }) },
    onError: () => msg.info('模板转 Skill 接口待接入'),
  })

  return (
    <>
      {msgCtx}
      <PageHeader title="模板聚类" subtitle="同结构≥3 篇对标支撑才可转 Skill" />
      <Card loading={q.isLoading}>
        {q.isError ? <EmptyIntegration description="模板接口待接入" onRefresh={() => q.refetch()} /> : (
          <List
            dataSource={q.data ?? []}
            locale={{ emptyText: '暂无模板' }}
            renderItem={(t) => (
              <List.Item
                actions={[
                  <Button key="skill" size="small" type="link" disabled={t.supported_count < 3} onClick={() => toSkill.mutate(t.id)}>转 Skill</Button>,
                ]}
              >
                <List.Item.Meta
                  title={<Space><Typography.Text>{t.cluster_key}</Typography.Text><Tag color={t.status === 'used' ? 'success' : 'default'}>{t.status}</Tag></Space>}
                  description={t.draft_md ? t.draft_md.slice(0, 80) : '暂无草案'}
                />
                <Badge count={t.supported_count} title="支撑对标篇数" />
              </List.Item>
            )}
          />
        )}
      </Card>
    </>
  )
}