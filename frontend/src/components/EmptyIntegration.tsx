import { Button, Empty } from 'antd'

interface EmptyIntegrationProps {
  description?: string
  onRefresh?: () => void
}

/** 后端接口尚未接入时的统一空态，明确提示“待接入”，不使用假数据。 */
export function EmptyIntegration({ description, onRefresh }: EmptyIntegrationProps) {
  return (
    <Empty
      image={Empty.PRESENTED_IMAGE_SIMPLE}
      description={description ?? '该模块后端接口待接入，暂无可展示数据。'}
      style={{ padding: '40px 0' }}
    >
      {onRefresh && (
        <Button size="small" onClick={onRefresh}>
          重试
        </Button>
      )}
    </Empty>
  )
}