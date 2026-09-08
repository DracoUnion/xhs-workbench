import { Card, Divider, Empty, List, Tag, Typography } from 'antd'
import { PageHeader } from '../../components/PageHeader'
import { EmptyIntegration } from '../../components/EmptyIntegration'

const EXECUTOR_OPTIONS = ['inline', 'celery']

export default function Settings() {
  return (
    <>
      <PageHeader title="设置" subtitle="Agent、执行与风控参数（后端未接入的部分显示待接入）" />
      <Card title="任务执行器">
        <Typography.Paragraph>
          当前运行场景为单机 inline（无需 Redis）；接入 Celery 后切为 <Tag>celery</Tag>。
        </Typography.Paragraph>
        <Typography.Text type="secondary">
          配置项：<code>RUN_EXECUTOR</code> = {EXECUTOR_OPTIONS.join(' / ')}。后端 <code>/settings</code> 接口尚未接入。
        </Typography.Text>
        <Divider style={{ margin: '12px 0' }} />
        <EmptyIntegration description="执行器/Agent 定义的后端配置接口待接入，届时可在此可视化调整。" />
      </Card>
      <Card title="Agent 定义" style={{ marginTop: 16 }}>
        <List
          dataSource={[
            { key: 'qianfan_collector', name: '千帆榜单采集' },
            { key: 'account_analyzer', name: '账号分析（评分）' },
            { key: 'note_analyzer', name: '笔记拆解' },
            { key: 'content_generator', name: '内容生成' },
            { key: 'content_reviewer', name: '内容审查' },
          ]}
          renderItem={(a) => (
            <List.Item>
              <Typography.Text code>{a.key}</Typography.Text>
              <Typography.Text>{a.name}</Typography.Text>
            </List.Item>
          )}
        />
        <Divider />
        <EmptyIntegration description="Agent 提示词/工具白名单/模型的后端配置接口待接入。" />
      </Card>
      <Card title="风控节奏" style={{ marginTop: 16 }}>
        <EmptyIntegration description="各动作 scope 的随机延迟区间等风控参数后端接口待接入。" />
      </Card>
    </>
  )
}