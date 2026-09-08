import axios, { type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../stores/auth'
import type { ApiErrorBody } from '../types/api'

export const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1'

export class ApiClientError extends Error {
  code: string
  details?: unknown

  constructor(message: string, code = 'UNKNOWN', details?: unknown) {
    super(message)
    this.name = 'ApiClientError'
    this.code = code
    this.details = details
  }
}

export const http = axios.create({
  baseURL: API_BASE,
  timeout: 30_000,
})

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const body: ApiErrorBody | undefined = error?.response?.data
    const code = body?.error?.code ?? error?.code ?? 'NETWORK_ERROR'
    const message = body?.error?.message ?? error?.message ?? '网络错误'
    const normalized = new ApiClientError(message, code, body?.error?.details)

    // 认证失败：触发全局跳登录（refresh 由 auth store 处理，失败在此清空）
    if (code === 'AUTH_REQUIRED' || code === 'TOKEN_INVALID' || code === 'AUTH_FAILED') {
      useAuthStore.getState().clear()
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(normalized)
  },
)

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const res = await http.request<T>(config)
  return res.data
}

export function errorMessage(err: unknown): string {
  if (err instanceof ApiClientError) return err.message
  if (err instanceof Error) return err.message
  return '未知错误'
}