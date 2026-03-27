import { create } from 'zustand'
import type { CounselStatus, RuleReport, StreamEvent, CounselStage } from '../lib/types'

interface StreamMessage {
  id: string
  timestamp: number
  counselName: string
  stage: CounselStage
  content: string
  type: 'thinking' | 'result' | 'error'
}

interface SessionState {
  activeView: 'mission_control' | 'history'
  sessionId: string | null
  ruleId: string | null
  status: 'idle' | 'connecting' | 'running' | 'complete' | 'error'
  counsel: CounselStatus[]
  stream: StreamMessage[]
  report: RuleReport | null
  stats: {
    totalTokens: number
    startedAt: number | null
    completedAt: number | null
  }
  error: string | null

  // Actions
  setActiveView: (view: 'mission_control' | 'history') => void
  startSession: (sessionId: string, ruleId: string) => void
  handleEvent: (event: StreamEvent) => void
  loadReport: (report: RuleReport) => void
  reset: () => void
}

const DEFAULT_COUNSEL: CounselStatus[] = [
  { name: 'amendment_counsel', displayName: 'Amendment Counsel', stage: 'specialist', status: 'waiting', tokenCount: 0, startedAt: null, completedAt: null },
  { name: 'reference_counsel', displayName: 'Reference Counsel', stage: 'specialist', status: 'waiting', tokenCount: 0, startedAt: null, completedAt: null },
  { name: 'structure_scope_counsel', displayName: 'Structure Counsel', stage: 'specialist', status: 'waiting', tokenCount: 0, startedAt: null, completedAt: null },
  { name: 'fidelity_counsel', displayName: 'Fidelity Counsel', stage: 'specialist', status: 'waiting', tokenCount: 0, startedAt: null, completedAt: null },
  { name: 'artifact_defender', displayName: 'Skeptic', stage: 'skeptic', status: 'waiting', tokenCount: 0, startedAt: null, completedAt: null },
  { name: 'chief_arbiter', displayName: 'Arbiter', stage: 'arbiter', status: 'waiting', tokenCount: 0, startedAt: null, completedAt: null },
]

let msgCounter = 0

export const useSessionStore = create<SessionState>((set) => ({
  activeView: 'mission_control',
  sessionId: null,
  ruleId: null,
  status: 'idle',
  counsel: DEFAULT_COUNSEL.map(c => ({ ...c })),
  stream: [],
  report: null,
  stats: { totalTokens: 0, startedAt: null, completedAt: null },
  error: null,

  setActiveView: (view) => set({ activeView: view }),

  startSession: (sessionId, ruleId) => set({
    activeView: 'mission_control',
    sessionId,
    ruleId,
    status: 'running',
    counsel: DEFAULT_COUNSEL.map(c => ({ ...c })),
    stream: [],
    report: null,
    stats: { totalTokens: 0, startedAt: Date.now(), completedAt: null },
    error: null,
  }),

  handleEvent: (event) => set((state) => {
    const counsel = [...state.counsel]
    const stream = [...state.stream]
    const stats = { ...state.stats }

    switch (event.type) {
      case 'counsel_start': {
        const idx = counsel.findIndex(c => c.name === event.counsel_name)
        if (idx !== -1) {
          counsel[idx] = { ...counsel[idx], status: 'active', startedAt: event.timestamp }
        }
        break
      }
      case 'counsel_chunk': {
        if (event.content && event.counsel_name) {
          // Append to last message from same counsel or create new
          const lastMsg = stream[stream.length - 1]
          if (lastMsg && lastMsg.counselName === event.counsel_name && lastMsg.type === 'thinking') {
            stream[stream.length - 1] = { ...lastMsg, content: lastMsg.content + event.content }
          } else {
            stream.push({
              id: `msg-${++msgCounter}`,
              timestamp: event.timestamp,
              counselName: event.counsel_name,
              stage: event.stage || 'specialist',
              content: event.content,
              type: 'thinking',
            })
          }
        }
        if (event.token_count) {
          stats.totalTokens += event.token_count
          const idx = counsel.findIndex(c => c.name === event.counsel_name)
          if (idx !== -1) {
            counsel[idx] = { ...counsel[idx], tokenCount: counsel[idx].tokenCount + event.token_count }
          }
        }
        break
      }
      case 'counsel_result': {
        const idx = counsel.findIndex(c => c.name === event.counsel_name)
        if (idx !== -1) {
          counsel[idx] = { ...counsel[idx], status: 'complete', completedAt: event.timestamp }
        }
        if (event.content && event.counsel_name) {
          stream.push({
            id: `msg-${++msgCounter}`,
            timestamp: event.timestamp,
            counselName: event.counsel_name,
            stage: event.stage || 'specialist',
            content: event.content,
            type: 'result',
          })
        }
        break
      }
      case 'report_complete': {
        stats.completedAt = event.timestamp
        return { counsel, stream, stats, report: event.report || null, status: 'complete' }
      }
      case 'error': {
        return { counsel, stream, stats, error: event.error || 'Unknown error', status: 'error' }
      }
    }

    return { counsel, stream, stats }
  }),

  loadReport: (report) => set({
    activeView: 'mission_control',
    report,
    status: 'complete',
    ruleId: report.rule_id,
    stats: { totalTokens: 0, startedAt: null, completedAt: Date.now() },
  }),

  reset: () => set({
    activeView: 'mission_control',
    sessionId: null,
    ruleId: null,
    status: 'idle',
    counsel: DEFAULT_COUNSEL.map(c => ({ ...c })),
    stream: [],
    report: null,
    stats: { totalTokens: 0, startedAt: null, completedAt: null },
    error: null,
  }),
}))
