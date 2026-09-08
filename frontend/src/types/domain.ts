// 业务领域类型：后端对应接口多尚未实现，页面以真实空态/待接入呈现，不伪造数据。

export interface RankingSource {
  key: string
  name: string
  page_max: number
  delay_scope: string
  enabled: boolean
}

export interface Account {
  id: number
  xhs_user_id: string
  nickname?: string | null
  fans?: number | null
  score?: number | null
  board_days?: number
  board_types?: number
  metrics?: AccountMetric | null
}

export interface AccountMetric {
  trade_score?: number
  conv_score?: number
  read_score?: number
  evidence_score?: number
  trust_bonus?: number
  low_fans_bonus?: number
  total?: number
  breakdown?: Record<string, unknown>
}

export interface Product {
  id: number
  xhs_id?: string
  account_id?: number
  direction_id?: number
  title?: string
  price_cents?: number
  sales?: number
  form?: string
  role?: string
  status?: string
  images?: ProductImage[]
}

export interface ProductImage {
  id: number
  url: string
  local_path?: string
  seq: number
}

export type DirectionStatus = '观察中' | '升温' | '已验证' | '降温' | '放弃'

export interface Direction {
  id: number
  name: string
  category?: string
  form?: string
  status: string
  evidence?: string
  picked_product_id?: number
}

export interface Keyword {
  id: number
  product_id: number
  word: string
  is_core: boolean
  a_to_z: boolean
  collect_comments: boolean
  pages_target: number
  collected_count: number
}

export interface Note {
  id: number
  note_id: string
  product_id: number
  title?: string
  body?: string
  topics?: string[]
  author?: string
  interactions?: { likes?: number; collects?: number; comments?: number }
  media_type: string
  analyzed: boolean
}

export interface Template {
  id: number
  product_id: number
  cluster_key: string
  supported_count: number
  draft_md?: string
  status: string
}

export interface Skill {
  id: number
  product_id: number
  name: string
  md: string
  files_whitelist: string[]
  rules: Record<string, unknown>
  status: string
  review_policy: string
  current_version: number
}

export interface ContentPackage {
  id: number
  skill_id: number
  seq: number
  title?: string
  body?: string
  topics?: string[]
  images?: Array<{ seq: number; type: string; path: string }>
  status: string
  rounds: number
}
