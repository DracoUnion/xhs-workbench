import { Tag } from 'antd'
import type { RunStatus } from '../types/api'

const STATUS_COLOR: Record<string, string> = {
  pending: 'default',
  running: 'processing',
  blocked: 'warning',
  done: 'success',
  failed: 'error',
  killed: 'default',
}

const STATUS_LABEL: Record<string, string> = {
  pending: '排队中',
  running: '运行中',
  blocked: '待审核',
  done: '完成',
  failed: '失败',
  killed: '已终止',
}

export function RunStatusTag({ status }: { status: RunStatus | string }) {
  const key = String(status)
  return (
    <Tag color={STATUS_COLOR[key] ?? 'default'}>
      {STATUS_LABEL[key] ?? key}
    </Tag>
  )
}