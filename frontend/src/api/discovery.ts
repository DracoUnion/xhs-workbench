import { request } from './http'
import type { RankingSource, Account, Product, Direction } from '../types/domain'
import type { ApiPage } from '../types/api'

const unwrap = <T>(res: { data: T }): T => res.data

// 注意：需求发现各接口后端尚未实现，页面捕获 404/501 后展示“待接入”空态。

export const listRankingSources = (): Promise<RankingSource[]> =>
  request<{ data: RankingSource[] }>({ url: '/ranking-sources' }).then(unwrap)

export const startRankingCollection = (sourceKeys: string[], pageMax?: number) =>
  request<{ data: unknown }>({ url: '/rankings/tasks', method: 'POST', data: { source_keys: sourceKeys, page_max: pageMax } }).then(unwrap)

export const listAccounts = (page = 1, pageSize = 20): Promise<ApiPage<Account>> =>
  request<ApiPage<Account>>({ url: '/accounts', params: { page, page_size: pageSize } })

export const getAccount = (id: number): Promise<Account> =>
  request<{ data: Account }>({ url: `/accounts/${id}` }).then(unwrap)

export const listProducts = (accountId?: number, page = 1, pageSize = 20): Promise<ApiPage<Product>> =>
  request<ApiPage<Product>>({ url: '/products', params: { account_id: accountId, page, page_size: pageSize } })

export const getProduct = (id: number): Promise<Product> =>
  request<{ data: Product }>({ url: `/products/${id}` }).then(unwrap)

export const listDirections = (): Promise<Direction[]> =>
  request<{ data: Direction[] }>({ url: '/directions' }).then(unwrap)