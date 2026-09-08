import { useQuery } from '@tanstack/react-query'
import { Card, Descriptions, Skeleton, Typography } from 'antd'
import { useParams } from 'react-router-dom'
import { getNote, getNoteAnalysis } from '../../../api/content'
import { errorMessage } from '../../../api/http'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

export default function NoteDetail() {
  const { id } = useParams()
  const noteId = Number(id)
  const note = useQuery({ queryKey: ['note', noteId], queryFn: () => getNote(noteId), enabled: !!noteId })
  const analysis = useQuery({ queryKey: ['note-analysis', noteId], queryFn: () => getNoteAnalysis(noteId), enabled: !!noteId })

  if (note.isLoading) return <><PageHeader title={`笔记 #${id}`} /><Skeleton active /></>
  if (note.isError) return (<><PageHeader title={`笔记 #${id}`} /><EmptyIntegration description="笔记接口待接入" /></>)

  return (
    <>
      <PageHeader title={note.data?.title ?? `笔记 #${id}`} subtitle="内容与单篇拆解" />
      <Card loading={analysis.isLoading}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="作者">{note.data?.author ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="类型">{note.data?.media_type}</Descriptions.Item>
          <Descriptions.Item label="互动">{JSON.stringify(note.data?.interactions ?? {})}</Descriptions.Item>
          <Descriptions.Item label="话题">{(note.data?.topics ?? []).join(' · ') || '-'}</Descriptions.Item>
        </Descriptions>
        <Typography.Paragraph>{note.data?.body}</Typography.Paragraph>
        <Typography.Title level={5}>单篇拆解</Typography.Title>
        {analysis.isError ? <EmptyIntegration description="拆解接口待接入" onRefresh={() => analysis.refetch()} /> : <pre style={{ background: '#fafafa', padding: 12, borderRadius: 6 }}>{JSON.stringify(analysis.data, null, 2)}</pre>}
      </Card>
    </>
  )
}