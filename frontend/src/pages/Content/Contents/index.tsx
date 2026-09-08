import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Card, InputNumber, Space, Table, Tag, message } from 'antd'
import { useState } from 'react'
import { generateContent, listContentPackages } from '../../../api/content'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

export default function Contents() {
  const qc = useQueryClient()
  const [msg, msgCtx] = message.useMessage()
  const [skillId, setSkillId] = useState<number | null>(null)
  const q = useQuery({ queryKey: ['contents'], queryFn: () => listContentPackages(undefined, undefined) })

  const gen = useMutation({
    mutationFn: (sid: number) => generateContent(sid, 1),
    onSuccess: () => { msg.success('已提交日更生成'); qc.invalidateQueries({ queryKey: ['contents'] }) },
    onError: () => msg.info('日更生成接口待接入'),
  })

  return (
    <>
      {msgCtx}
      <PageHeader
        title="内容包队列"
        subtitle="日更生成 → 独立审查"
        extra={
          <Space>
            <InputNumber placeholder="Skill ID" min={1} value={skillId} onChange={(v) => setSkillId(v)} />
            <Button type="primary" disabled={!skillId} loading={gen.isPending} onClick={() => skillId && gen.mutate(skillId)}>生成内容包</Button>
          </Space>
        }
      />
      <Card loading={q.isLoading}>
        {q.isError ? <EmptyIntegration description="内容包接口待接入" onRefresh={() => q.refetch()} /> : (
          <Table
            rowKey="id"
            dataSource={q.data ?? []}
            pagination={false}
            size="small"
            columns={[
              { title: 'ID', dataIndex: 'id', width: 70 },
              { title: 'Skill', dataIndex: 'skill_id', width: 90 },
              { title: '序号', dataIndex: 'seq', width: 70 },
              { title: '标题', dataIndex: 'title' },
              { title: '状态', dataIndex: 'status', width: 110, render: (v) => <Tag color={v === 'approved' ? 'success' : v === 'rejected' ? 'error' : 'processing'}>{v}</Tag> },
              { title: '轮次', dataIndex: 'rounds', width: 70 },
            ]}
          />
        )}
      </Card>
    </>
  )
}