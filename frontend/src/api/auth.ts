import { request } from './http'
import type { TokenResponse, User } from '../types/api'

interface TokenData {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token: string
}

export const login = (username: string, password: string): Promise<TokenResponse> =>
  request<TokenData>({ url: '/auth/login', method: 'POST', data: { username, password } })

export const refresh = (refreshToken: string): Promise<TokenResponse> =>
  request<TokenData>({ url: '/auth/refresh', method: 'POST', data: { refresh_token: refreshToken } })

export const me = (): Promise<User> => request<User>({ url: '/auth/me' })