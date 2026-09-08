import { request } from './http'
import type { DashboardSummary } from '../types/api'

export const getDashboardSummary = (): Promise<DashboardSummary> =>
  request<{ data: DashboardSummary }>({ url: '/dashboard/summary' }).then((r) => r.data)