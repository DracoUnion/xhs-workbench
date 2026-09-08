import { request } from './http'
import type { XhsStatus } from '../types/api'

export const getStatus = (): Promise<XhsStatus> =>
  request<{ data: XhsStatus }>({ url: '/xhs/status' }).then((r) => r.data)

export const setCookies = (cookie: string): Promise<XhsStatus> =>
  request<{ data: XhsStatus }>({ url: '/xhs/cookies', method: 'PUT', data: { cookie } }).then((r) => r.data)

export const clearCookies = (): Promise<Record<string, unknown>> =>
  request<{ data: Record<string, unknown> }>({ url: '/xhs/cookies', method: 'DELETE' }).then((r) => r.data)