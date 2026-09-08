import { useState } from 'react'
import { Alert, Button, Descriptions, Input, Modal, Space, Tag, Typography } from 'antd'
import type { ReviewPoint } from '../types/api'

interface ReviewPointModalProps {
  point: ReviewPoint | null
  loading?: boolean
  onClose: () => void
  onSubmit: (action: 'passed' | 'rejected', note?: string) => void
}

export function ReviewPointModal({ point, loading, onClose, onSubmit }: ReviewPointModalProps) {
  const [note, setNote] = useState('')
  const [mode, setMode] = useState<'passed' | 'rejected'>('passed')

  const rtypeColor = point?.rtype === 'REVIEW' ? 'warning' : point?.rtype === 'MANUAL' ? 'blue' : 'default'

  return (
    <Modal
      title="审核点"
      open={!!point}
      onCancel={onClose}
      destroyOnClose
      width={640}
      footer={
        <Space>
          <Button onClick={onClose} disabled={loading}>
            关闭
          </Button>
          <Button
            danger
            disabled={loading}
            onClick={() => {
              setMode('rejected')
              onSubmit('rejected', note || undefined)
            }}
          >
            驳回
          </Button>
          <Button
            type="primary"
            disabled={loading}
            onClick={() => {
              setMode('passed')
              onSubmit('passed', note || undefined)
            }}
          >
            通过并继续
          </Button>
        </Space>
      }
    >
      {point && (
        <>
          <Descriptions size="small" column={1} style={{ marginBottom: 12 }}>
            <Descriptions.Item label="类型">
              <Tag color={rtypeColor}>{point.rtype}</Tag>
              <Tag>{point.agent_key}</Tag>
              <Typography.Text type="secondary">任务 #{point.run_id}</Typography.Text>
            </Descriptions.Item>
          </Descriptions>
          <Alert
            type="info"
            showIcon
            message="请核对以下信息后决定是否放行"
            style={{ marginBottom: 12 }}
          />
          <pre
            style={{
              background: '#f5f5f5',
              padding: 12,
              borderRadius: 6,
              maxHeight: 220,
              overflow: 'auto',
              fontSize: 12,
              margin: 0,
            }}
          >
            {JSON.stringify(point.payload, null, 2)}
          </pre>
          <Input.TextArea
            rows={3}
            placeholder="备注（可选）"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            style={{ marginTop: 12 }}
          />
        </>
      )}
    </Modal>
  )
}