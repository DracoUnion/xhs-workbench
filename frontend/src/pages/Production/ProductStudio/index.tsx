import { useQuery } from '@tanstack/react-query'
import { Card, Descriptions, Empty, Steps, Typography } from 'antd'
import { useParams } from 'react-router-dom'
import { getDesignDoc, listMaterials } from '../../../api/production'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

const stages = ['requirements', 'prototype', 'ui', 'logic', 'accept']

export default function ProductStudio() {
  const { id } = useParams()
  const productId = Number(id)
  const design = useQuery({ queryKey: ['design-doc', productId], queryFn: () => getDesignDoc(productId), enabled: !!productId })
  const materials = useQuery({ queryKey: ['materials', productId], queryFn: () => listMaterials(productId), enabled: !!productId })

  return (
    <>
      <PageHeader title={`产品工作室 #${id}`} subtitle="资料整理、结构制作与逐步验收" />
      <Card title="开发阶段" loading={design.isLoading}>
        {design.isError ? <EmptyIntegration description="产品设计接口待接入" /> : <Steps current={Math.max(0, stages.indexOf(design.data?.stage ?? 'requirements'))} items={stages.map((title) => ({ title }))} />}
      </Card>
      <Card title="资料清单" style={{ marginTop: 16 }} loading={materials.isLoading}>
        {materials.isError ? <EmptyIntegration description="资料接口待接入" /> : materials.data?.length ? materials.data.map((m) => <Descriptions key={m.id} size="small" column={2}><Descriptions.Item label="文件">{m.filename}</Descriptions.Item><Descriptions.Item label="状态">{m.ingest_status}</Descriptions.Item></Descriptions>) : <Empty description="暂无资料" />}
      </Card>
      <Card title="验收说明" style={{ marginTop: 16 }}>
        <Typography.Paragraph type="secondary">按模块制作，逐项核对文件完整性、链接可用性与用户上手体验。验收清单接口接入后可在此提交结果。</Typography.Paragraph>
      </Card>
    </>
  )
}