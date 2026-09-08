import { useQuery } from '@tanstack/react-query'
import { Card, Descriptions, Empty, Image, Typography } from 'antd'
import { useParams } from 'react-router-dom'
import { getProduct } from '../../../api/discovery'
import { listProductImages } from '../../../api/production'
import { errorMessage } from '../../../api/http'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyIntegration } from '../../../components/EmptyIntegration'

export default function ProductDetail() {
  const { id } = useParams()
  const productId = Number(id)
  const product = useQuery({ queryKey: ['product', productId], queryFn: () => getProduct(productId), enabled: !!productId })
  const images = useQuery({ queryKey: ['product-images', productId], queryFn: () => listProductImages(productId), enabled: !!productId })

  if (product.isError) {
    return (
      <>
        <PageHeader title={`商品 #${id}`} />
        <EmptyIntegration description="商品接口待接入" onRefresh={() => { product.refetch(); images.refetch() }} />
      </>
    )
  }

  const p = product.data
  return (
    <>
      <PageHeader title={p?.title ?? `商品 #${id}`} subtitle="详情与图片校验" />
      <Card loading={product.isLoading}>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="价格(分)">{p?.price_cents ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="销量">{p?.sales ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="形态">{p?.form ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="角色">{p?.role ?? '-'}</Descriptions.Item>
        </Descriptions>
      </Card>
      <Card title="图片" style={{ marginTop: 16 }}>
        {images.isError ? (
          <EmptyIntegration description="图片接口待接入" />
        ) : (images.data?.length
          ? (
            <Image.PreviewGroup>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {images.data.map((img) => (
                  <Image key={img.id} width={120} src={img.url} style={{ borderRadius: 6 }} />
                ))}
              </div>
            </Image.PreviewGroup>
          ) : <Empty description="暂无图片" />)}
      </Card>
    </>
  )
}