import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Card, Input, Space, Tag, message } from 'antd'
import { useParams } from 'react-router-dom'
import { getSkill, testSkill, updateSkill } from '../../../api/content'
import { errorMessage } from '../../../api/http'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

export default function SkillEditor() {
  const { id } = useParams()
  const skillId = Number(id)
  const qc = useQueryClient()
  const [msg, msgCtx] = message.useMessage()
  const [md, setMd] = useState('')

  const skill = useQuery({ queryKey: ['skill', skillId], queryFn: () => getSkill(skillId), enabled: !!skillId })

  const save = useMutation({
    mutationFn: (body: string) => updateSkill(skillId, { md: body }),
    onSuccess: () => { msg.success('已保存'); qc.invalidateQueries({ queryKey: ['skill', skillId] }) },
    onError: () => msg.info('Skill 接口待接入'),
  })

  const test = useMutation({
    mutationFn: () => testSkill(skillId),
    onSuccess: () => msg.success('已触发试跑'),
    onError: () => msg.info('试跑接口待接入'),
  })

  if (skill.isError) return (<><PageHeader title={`Skill #${id}`} /><EmptyIntegration description="Skill 接口待接入" /></>)

  const current = md || skill.data?.md || ''
  return (
    <>
      {msgCtx}
      <PageHeader
        title={skill.data?.name ?? `Skill #${id}`}
        subtitle="Markdown 编辑 · 文件白名单 · 试跑/上线"
        extra={<Space><Button loading={test.isPending} onClick={() => test.mutate()}>试跑</Button><Button type="primary" disabled={!skill.data || skill.data.status === 'active'} onClick={() => save.mutate(current)}>保存</Button></Space>}
      />
      <Alert type="info" showIcon style={{ marginBottom: 12 }} message="按规则保存：文件白名单仅允许引用 Skill 指定的产品事实；保存/上线接口接入后生效。" />
      <Card loading={skill.isLoading} title={<Space>内容规范 <Tag color={skill.data?.status === 'active' ? 'success' : 'default'}>{skill.data?.status}</Tag></Space>}>
        <Input.TextArea
          value={current}
          onChange={(e) => setMd(e.target.value)}
          autoSize={{ minRows: 18, maxRows: 30 }}
          placeholder="SKILL.md 内容…"
        />
      </Card>
      <Card title="文件白名单" style={{ marginTop: 16 }}>
        {(skill.data?.files_whitelist ?? []).map((f) => <Tag key={f} color="blue">{f}</Tag>)}
        {(skill.data?.files_whitelist ?? []).length === 0 && <Alert type="warning" showIcon message="尚未配置可引用文件白名单" />}
      </Card>
    </>
  )
}