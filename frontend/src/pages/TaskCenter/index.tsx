import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  Card,
  Drawer,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import { ReloadOutlined, PlusOutlined, PlayCircleOutlined, StopOutlined } from '@ant-design/icons'
import {
  abortTask,
  actReviewPoint,
  createTask,
  getTaskMessages,
  listReviewPoints,
  listTasks,
  resumeTask,
} from '../../api/tasks'
import { errorMessage } from '../../api/http'
import { PageHeader } from '../../components/PageHeader'
import { RunStatusTag } from '../../components/RunStatusTag'
import { ReviewPointModal } from '../../components/ReviewPointModal'
import { useTaskStore } from '../../stores/tasks'
import type { AgentRun, ReviewPoint } from '../../types/api'

const AGENTS = [
  { key: 'qianfan_collector', name: '千帆榜单采集' },
  { key: 'account_analyzer', name: '账号分析' },
  { key: 'note_analyzer', name: '笔记拆解' },
  { key: 'content_generator', name: '内容生成' },
  { key: 'content_reviewer', name: '内容审查' },
]

interface CreateForm {
  agent_key: string
  context?: string
  product_id?: number
}

export default function TaskCenter() {
  const qc = useQueryClient()
  const [msg, msgCtx] = message.useMessage()
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState<string>()
  const [createOpen, setCreateOpen] = useState(false)
  const [selected, setSelected] = useState<AgentRun | null>(null)
  const [messages, setMessages] = useState<Record<string, unknown>[]>([])
  const [messageOpen, setMessageOpen] = useState(false)
  const [reviewPoint, setReviewPoint] = useState<ReviewPoint | null>(null)
  const [form] = Form.useForm<CreateForm>()

  const version = useTaskStore((s) => s.version)
  const liveRuns = useTaskStore((s) => s.liveRuns)

  const tasks = useQuery({
    queryKey: ['tasks', page, status],
    queryFn: () => listTasks({ page, page_size: 20, status }),
  })

  const reviews = useQuery({
    queryKey: ['review-points'],
    queryFn: () => listReviewPoints(true),
  })

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['tasks'] })
    qc.invalidateQueries({ queryKey: ['review-points'] })
  }
  useEffect(refresh, [version, qc])

  const createMut = useMutation({
    mutationFn: (body: CreateForm) => createTask({ agent_key: body.agent_key, context: body.context, product_id: body.product_id ?? null }),
    onSuccess: () => {
      msg.success('已创建任务')
      setCreateOpen(false)
      form.resetFields()
      refresh()
    },
    onError: (err) => msg.error(errorMessage(err)),
  })

  const resumeMut = useMutation({
    mutationFn: (id: number) => resumeTask(id),
    onSuccess: () => msg.success('已恢复任务'),
    onError: (err) => msg.error(errorMessage(err)),
    onSettled: refresh,
  })

  const abortMut = useMutation({
    mutationFn: (id: number) => abortTask(id),
    onSuccess: () => msg.success('已终止任务'),
    onError: (err) => msg.error(errorMessage(err)),
    onSettled: refresh,
  })

  const reviewMut = useMutation({
    mutationFn: ({ id, action, note }: { id: number; action: 'passed' | 'rejected'; note?: string }) => actReviewPoint(id, action, note),
    onSuccess: () => {
      msg.success('已处理审核点')
      setReviewPoint(null)
      refresh()
    },
    onError: (err) => msg.error(errorMessage(err)),
  })

  const openMessages = async (run: AgentRun) => {
    setSelected(run)
    try {
      setMessages(await getTaskMessages(run.id))
    } catch (err) {
      msg.warning(errorMessage(err))
      setMessages([])
    }
    setMessageOpen(true)
  }

  const rows = useMemo(
    () =>
      (tasks.data?.data ?? []).map((run) => {
        const live = liveRuns[run.id]
        return { ...run, status: live?.status ?? run.status, tool: live?.tool }
      }),
    [tasks.data, liveRuns],
  )

  return (
    <>
      {msgCtx}
      <PageHeader
        title="任务中心"
        subtitle="Agent 运行进度、人工审核点"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => refresh()}>刷新</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>发起任务</Button>
          </Space>
        }
      />
      <Card
        title={
          <Space>
            任务列表
            <Badge count={reviews.data?.length ?? 0} overflowCount={99} showZero={false}>
              <Tag color="warning">待审核</Tag>
            </Badge>
          </Space>
        }
      >
        <Space wrap style={{ marginBottom: 12 }}>
          <Select
            allowClear
            placeholder="按状态筛选"
            style={{ width: 160 }}
            value={status}
            onChange={(v) => {
              setStatus(v)
              setPage(1)
            }}
            options={['pending', 'running', 'blocked', 'done', 'failed', 'killed'].map((s) => ({
              value: s,
              label: s,
            }))}
          />
          <Button type="link" onClick={() => { if (selected) openMessages(selected) }} disabled={!selected}>查看已选任务消息</Button>
        </Space>
        <Table<AgentRun>
          rowKey="id"
          loading={tasks.isLoading}
          dataSource={rows}
          size="small"
          pagination={{
            current: page,
            pageSize: 20,
            total: tasks.data?.meta.total ?? 0,
            onChange: setPage,
            showSizeChanger: false,
          }}
          onRow={(run) => ({
            onClick: () => setSelected(run),
            style: { cursor: 'pointer' },
          })}
          columns={[
            { title: 'ID', dataIndex: 'id', width: 70 },
            { title: 'Agent', dataIndex: 'agent_key', width: 160 },
            { title: '状态', dataIndex: 'status', width: 100, render: (s: string, r) => <RunStatusTag status={s} /> },
            { title: '当前步骤', dataIndex: 'tool', width: 140, render: (tool?: string) => tool ?? '-' },
            {
              title: '操作',
              key: 'ops',
              width: 150,
              render: (_, run) => (
                <Space size={4}>
                  <Button size="small" onClick={(e) => { e.stopPropagation(); openMessages(run) }}>消息</Button>
                  {run.status === 'blocked' && (
                    <Button size="small" onClick={(e) => { e.stopPropagation(); resumeMut.mutate(run.id) }}>
                      恢复
                    </Button>
                  )}
                  {['pending', 'running', 'blocked'].includes(String(run.status)) && (
                    <Button size="small" danger onClick={(e) => { e.stopPropagation(); Modal.confirm({ title: '终止该任务？', onOk: () => abortMut.mutate(run.id) }) }}>
                      终止
                    </Button>
                  )}
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal title="发起任务" open={createOpen} onOk={() => form.submit()} confirmLoading={createMut.isPending} onCancel={() => setCreateOpen(false)}>
        <Form form={form} layout="vertical" onFinish={(v: CreateForm) => createMut.mutate(v)} initialValues={{ agent_key: 'account_analyzer' }}>
          <Form.Item name="agent_key" label="Agent" rules={[{ required: true }]}>
            <Select options={AGENTS.map((a) => ({ value: a.key, label: a.name }))} />
          </Form.Item>
          <Form.Item name="product_id" label="关联商品 ID（可选）">
            <Input type="number" placeholder="留空则不限商品" />
          </Form.Item>
          <Form.Item name="context" label="任务描述">
            <Input.TextArea rows={3} placeholder="给 Agent 的初始上下文" />
          </Form.Item>
        </Form>
      </Modal>

      <ReviewPointModal
        point={reviewPoint}
        loading={reviewMut.isPending}
        onClose={() => setReviewPoint(null)}
        onSubmit={(action, note) => reviewPoint && reviewMut.mutate({ id: reviewPoint.id, action, note })}
      />

      <Drawer title={`任务 #${selected?.id ?? ''} 消息`} open={messageOpen} onClose={() => setMessageOpen(false)} width={640}>
        <Typography.Paragraph style={{ fontSize: 12 }} type="secondary">
          展示 agent_runs.messages 原始对话（含工具调用与结果）。数量较多时仅截取，完整数据可在数据库中查看。
        </Typography.Paragraph>
        {messages.map((m, i) => (
          <pre key={i} style={{ background: '#fafafa', padding: 8, borderRadius: 4, fontSize: 11, marginBottom: 8 }}>
            {JSON.stringify(m, null, 2)}
          </pre>
        ))}
        {messages.length === 0 && <Alert type="info" showIcon message="该任务暂无消息记录。" />}
      </Drawer>
    </>
  )
}