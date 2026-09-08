import { request } from './http'
import type { Product, ProductImage } from '../types/domain'

const unwrap = <T>(res: { data: T }): T => res.data
// 产品制作接口后端部分未实现：捕获 404/501 后前端展示“待接入”空态。

export interface MaterialMeta {
  id: number
  filename?: string
  mime?: string
  size_bytes?: number
  ingest_status?: string
}

export interface DesignDoc {
  id: number
  stage: string
  repo_url?: string
  build_path?: string
}

export const promoteProduct = (id: number): Promise<Product> =>
  request<{ data: Product }>({ url: `/products/${id}`, method: 'PATCH', data: { role: 'self-made' } }).then(unwrap)

export const listMaterials = (productId: number): Promise<MaterialMeta[]> =>
  request<{ data: MaterialMeta[] }>({ url: `/products/${productId}/materials` }).then(unwrap)

export const uploadMaterial = (productId: number, form: FormData): Promise<MaterialMeta> =>
  request<{ data: MaterialMeta }>({ url: `/products/${productId}/materials`, method: 'POST', data: form }).then(unwrap)

export const getDesignDoc = (productId: number): Promise<DesignDoc> =>
  request<{ data: DesignDoc }>({ url: `/products/${productId}/design` }).then(unwrap)

export const listProductImages = (id: number): Promise<ProductImage[]> =>
  request<{ data: ProductImage[] }>({ url: `/products/${id}/images` }).then(unwrap)