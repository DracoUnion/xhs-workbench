import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import * as authApi from '../api/auth'
import type { User } from '../types/api'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  setTokens: (access: string, refresh: string) => void
  setUser: (user: User) => void
  login: (username: string, password: string) => Promise<void>
  refresh: () => Promise<boolean>
  logout: () => void
  clear: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,

      setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),
      setUser: (user) => set({ user }),

      login: async (username, password) => {
        const tokens = await authApi.login(username, password)
        set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token })
        const me = await authApi.me()
        set({ user: me })
      },

      refresh: async () => {
        const rt = get().refreshToken
        if (!rt) return false
        try {
          const tokens = await authApi.refresh(rt)
          get().setTokens(tokens.access_token, tokens.refresh_token)
          return true
        } catch {
          return false
        }
      },

      logout: () => {
        set({ accessToken: null, refreshToken: null, user: null })
      },

      clear: () => {
        set({ accessToken: null, refreshToken: null, user: null })
      },
    }),
    { name: 'xhs-auth' },
  ),
)