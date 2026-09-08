import { create } from 'zustand'
import type { ReviewPoint, WsEvent } from '../types/api'

interface TasksState {
  connected: boolean
  version: number
  liveRuns: Record<number, { status: string; tool?: string; ok?: boolean }>
  blockedPoints: ReviewPoint[]
  lastEvent: WsEvent | null
  setConnected: (v: boolean) => void
  applyEvent: (ev: WsEvent) => void
  setBlockedPoints: (points: ReviewPoint[]) => void
}

export const useTaskStore = create<TasksState>((set) => ({
  connected: false,
  version: 0,
  liveRuns: {},
  blockedPoints: [],
  lastEvent: null,

  setConnected: (v) => set({ connected: v }),

  applyEvent: (ev) => {
    const runId = Number(ev.data?.run_id)
    const livePatch = runId && runId > 0
      ? { [String(runId)]: { status: ev.type.replace('run.', ''), tool: ev.data?.tool as string | undefined, ok: ev.data?.ok as boolean | undefined } }
      : {}
    set((s) => ({
      version: s.version + 1,
      lastEvent: ev,
      liveRuns: { ...s.liveRuns, ...livePatch },
    }))
  },

  setBlockedPoints: (points) => set({ blockedPoints: points }),
}))