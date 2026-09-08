import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Card, Form, Input, InputNumber, Space, Switch, Table, Tag, message } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { createKeyword, listKeywords, startKeywordCollection } from '../../../api/content'
import { errorMessage } from '../../../api/http'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'
import type { Keyword } from '../../../types/domain'

export default function Keywords() {
  const qc = useQueryClient()
  const [msg, msgCtx] = message.useMessage()
  const [form] = Form.useForm<{ word: string; product_id: number; is_core: boolean }>()
  const q = useQuery({ queryKey: ['keywords'], queryFn: () => listKeywords(0) })

  const createMut = useMutation({
    mutationFn: (body: Partial<Keyword>) => createKeyword(body),
    onSuccess: () => { msg.success('已添加关键词'); form.resetFields(); qc.invalidateQueries({ queryKey: ['keywords'] }) },
    onError: () => msg.info('关键词接口待接入'),
  })

  const collect = useMutation({
    mutationFn: (id: number) => startKeywordCollection(id),
    onSuccess: () => msg.success('已提交对标采集'),
    onError: () => msg.info('对标采集接口待接入'),
  })

  return (
    <>
      {msgCtx}
      <PageHeader title="关键词布局" subtitle="七维研究关键词 · A-Z 扩展 · 评论采集" />
      <Card>
        <Form form={form} layout="inline" onFinish={(v) => createMut.mutate({ word: v.word, product_id: v.product_id, is_core: v.is_core ?? false })} style={{ marginBottom: 16 }}>
          <Form.Item name="product_id" rules={[{ required: true, message: '商品 ID' }]}><InputNumber placeholder="商品 ID" min={1} /></Form.Item>
          <Form.Item name="word" rules={[{ required: true, message: '关键词' }]}><Input placeholder="关键词" style={{ width: 200 }} /></Form.Item>
          <Form.Item name="is_core" valuePropName="checked"><Switch checkedChildren="核心" unCheckedChildren="普通" /></Form.Item>
          <Button type="primary" icon={<PlusOutlined />} htmlType="submit" loading={createMut.isPending}>添加</Button>
        </Form>
        {q.isError ? <EmptyIntegration description="关键词接口待接入" onRefresh={() => q.refetch()} /> : (
          <Table
            rowKey="id"
            dataSource={q.data ?? []}
            pagination={false}
            size="small"
            columns={[
              { title: '词', dataIndex: 'word' },
              { title: '类型', width: 90, render: (_, r) => <Tag color={r.is_core ? 'gold' : 'default'}>{r.is_core ? '核心' : '普通'}</Tag> },
              { title: '目标篇数', dataIndex: 'pages_target', width: 110 },
              { title: '已采', dataIndex: 'collected_count', width: 90 },
              { title: 'A-Z', width: 70, render: (_, r) => (r.a_to_z ? '开' : '关') },
              { title: '操作', width: 110, render: (_, r) => <Button size="small" type="link" onClick={() => collect.mutate(r.id)}>发起采集</Button> },
            ]}
          />
        )}
      </Card>
    </>
  )
}