import { Button, Result } from 'antd'
import { useNavigate } from 'react-router-dom'

export default function NotFound() {
  const navigate = useNavigate()
  return (
    <Result
      status="404"
      title="404"
      subTitle="页面不存在或尚未实现"
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          返回工作台
        </Button>
      }
    />
  )
}