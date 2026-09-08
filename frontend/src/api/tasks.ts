import { request } from './http'
import type { AgentRun, ApiPage, ReviewPoint } from '../types/api'

export interface CreateTaskPayload {
  agent_key: string
  product_id?: number | null
  context?: string
}

export interface TaskListParams {
  status?: string
  agent_key?: string
  product_id?: number
  page?: number
  page_size?: number
}

const unwrap = <T>(res: { data: T }): T => res.data

export const listTasks = (params: TaskListParams): Promise<ApiPage<AgentRun>> =>
  request<ApiPage<AgentRun>>({ url: '/tasks', params })

export const getTask = (id: number): Promise<AgentRun> =>
  request<{ data: AgentRun }>({ url: `/tasks/${id}` }).then(unwrap)

export const getTaskMessages = (id: number): Promise<Record<string, unknown>[]> =>
  request<{ data: Record<string, unknown>[] }>({ url: `/tasks/${id}/messages` }).then((r) => r.data)

export const createTask = (body: CreateTaskPayload): Promise<{ run_id: number; run_uuid: string; mode: string }> =>
  request({ url: '/tasks', method: 'POST', data: body })

export const resumeTask = (id: number): Promise<{ run_id: number; mode: string }> =>
  request<{ data: { run_id: number; mode: string } }>({ url: `/tasks/${id}/resume`, method: 'POST' }).then((r) => r.data)

export const abortTask = (id: number): Promise<AgentRun> =>
  request<{ data: AgentRun }>({ url: `/tasks/${id}/abort`, method: 'POST' }).then(unwrap)

export const listReviewPoints = (pendingOnly = true): Promise<ReviewPoint[]> =>
  request<{ data: ReviewPoint[] }>({ url: '/review-points', params: { pending_only: pendingOnly } }).then((r) => r.data)

export const actReviewPoint = (
  id: number,
  action: 'passed' | 'rejected',
  note?: string,
): Promise<Record<string, unknown>> =>
  request<{ data: Record<string, unknown> }>({
    url: `/review-points/${id}`,
    method: 'PATCH',
    data: { action, note },
  }).then((r) => r.data)