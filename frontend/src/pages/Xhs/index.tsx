import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Card, Descriptions, Divider, Form, Input, Modal, Space, Statistic, Tag, Typography, message } from 'antd'
import { clearCookies, getStatus, setCookies } from '../../api/xhs'
import { errorMessage } from '../../api/http'
import { PageHeader } from '../../components/PageHeader'

export default function Xhs() {
  const qc = useQueryClient()
  const [msg, msgCtx] = message.useMessage()
  const [form] = Form.useForm<{ cookie: string }>()

  const statusQ = useQuery({ queryKey: ['xhs', 'status'], queryFn: getStatus })
  const status = statusQ.data

  const setMut = useMutation({
    mutationFn: (cookie: string) => setCookies(cookie),
    onSuccess: () => {
      msg.success('cookie 已保存')
      form.resetFields()
      qc.invalidateQueries({ queryKey: ['xhs'] })
    },
    onError: (err) => msg.error(errorMessage(err)),
  })

  const clearMut = useMutation({
    mutationFn: () => clearCookies(),
    onSuccess: () => {
      msg.success('已清除登录态')
      qc.invalidateQueries({ queryKey: ['xhs'] })
    },
    onError: (err) => msg.error(errorMessage(err)),
  })

  return (
    <>
      {msgCtx}
      <PageHeader title="小红书登录态" subtitle="xhs-cli 浏览器采集所需的 cookie 管理" />
      <Card loading={statusQ.isLoading}>
        {statusQ.isError ? (
          <Alert type="info" showIcon message="登录态接口暂不可用" description={errorMessage(statusQ.error)} />
        ) : (
          <>
            <Statistic
              title="是否已登录"
              value={status?.authenticated ? '已登录' : '未登录'}
              valueStyle={{ color: status?.authenticated ? '#52c41a' : '#ff4d4f' }}
            />
            <Divider />
            <Descriptions column={1} size="small">
              <Descriptions.Item label="必需字段">
                {status?.required?.map((k) => <Tag key={k}>{k}</Tag>)}
              </Descriptions.Item>
              <Descriptions.Item label="已就绪字段">
                {status?.present?.length
                  ? status.present.map((k) => <Tag key={k} color="success">{k}</Tag>)
                  : <Typography.Text type="secondary">无</Typography.Text>}
              </Descriptions.Item>
              <Descriptions.Item label="cookie 来源">{status?.source}</Descriptions.Item>
              <Descriptions.Item label="cookie 文件">{status?.cookie_file}</Descriptions.Item>
            </Descriptions>
          </>
        )}
      </Card>

      <Card title="下发 cookie（管理员）" style={{ marginTop: 16 }}>
        <Form<{ cookie: string }> form={form} layout="vertical" onFinish={(v) => setMut.mutate(v.cookie)}>
          <Form.Item
            name="cookie"
            rules={[{ required: true, message: '请粘贴 cookie header' }]}
            extra="cookie header 字符串，如 a1=...; web_session=...。完整值不会在本页回显。"
          >
            <Input.TextArea rows={4} placeholder="粘贴 cookie header" />
          </Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={setMut.isPending}>保存</Button>
            <Button
              danger
              loading={clearMut.isPending}
              onClick={() =>
                Modal.confirm({
                  title: '清除小红书登录态？',
                  content: '清除后需重新登录才能恢复采集功能。',
                  onOk: () => clearMut.mutate(),
                })
              }
            >
              清除登录态
            </Button>
          </Space>
        </Form>
      </Card>
    </>
  )
}