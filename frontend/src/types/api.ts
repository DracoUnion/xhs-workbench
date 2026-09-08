export interface User {
  id: number
  username: string
  role: 'admin' | 'operator' | string
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token: string
}

export type RunStatus = 'pending' | 'running' | 'blocked' | 'done' | 'failed' | 'killed'

export interface AgentRun {
  id: number
  run_uuid: string
  agent_key: string
  product_id?: number | null
  status: RunStatus | string
  result?: Record<string, unknown> | null
  error?: Record<string, unknown> | null
  started_at?: string | null
  finished_at?: string | null
  continue_at?: string | null
  created_at?: string | null
  messages?: Array<Record<string, unknown>>
  tool_calls?: Array<Record<string, unknown>>
}

export interface ReviewPoint {
  id: number
  run_id: number
  agent_key: string
  rtype: 'AUTO' | 'REVIEW' | 'MANUAL' | string
  payload: Record<string, unknown>
  action: 'pending' | 'passed' | 'rejected' | string
  created_at?: string | null
}

export interface DashboardSummary {
  date: string
  accounts_today: number
  products_today: number
  directions: Array<{
    id: number
    name: string
    status: string
    accounts: number
    price_range: [number, number]
    max_sales: number
    suggestion?: string
  }>
  market?: { accelerating: number; cooling: number }
  recent_runs: AgentRun[]
}

export interface XhsStatus {
  authenticated: boolean
  required: string[]
  present: string[]
  cookie_file: string
  source: string
}

export interface WsEvent {
  type: 'run.progress' | 'run.blocked' | 'run.done' | 'run.failed' | 'device.lock' | string
  data: Record<string, unknown>
}

export interface PageMeta {
  total: number
  page: number
  page_size: number
}

export interface ApiErrorBody {
  error: { code: string; message: string; details?: unknown }
}

export interface ApiPage<T> {
  data: T[]
  meta: PageMeta
}
