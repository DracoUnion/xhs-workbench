import { useEffect } from 'react'
import { useAuthStore } from '../stores/auth'
import { useTaskStore } from '../stores/tasks'

const WS_BASE = import.meta.env.VITE_WS_BASE ?? '/ws/tasks'
const MAX_BACKOFF = 30_000

/** 连接 /ws/tasks 实时任务通道：断线指数退避重连，组件卸载清理。 */
export function useTaskWebSocket(): void {
  const token = useAuthStore((s) => s.accessToken)

  useEffect(() => {
    if (!token) return
    let ws: WebSocket | undefined
    let stopped = false
    let retries = 0

    const connect = () => {
      if (stopped) return
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const url = `${proto}://${window.location.host}${WS_BASE}?token=${encodeURIComponent(token)}`
      ws = new WebSocket(url)
      ws.onopen = () => {
        retries = 0
        useTaskStore.getState().setConnected(true)
      }
      ws.onmessage = (ev: MessageEvent) => {
        try {
          useTaskStore.getState().applyEvent(JSON.parse(ev.data as string))
        } catch {
          /* 忽略无法解析帧 */
        }
      }
      ws.onclose = () => {
        useTaskStore.getState().setConnected(false)
        if (!stopped) {
          const delay = Math.min(MAX_BACKOFF, 1000 * 2 ** retries++)
          setTimeout(connect, delay)
        }
      }
      ws.onerror = () => ws?.close()
    }

    connect()
    return () => {
      stopped = true
      ws?.close()
    }
  }, [token])
}