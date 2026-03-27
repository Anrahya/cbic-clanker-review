import { useRef, useEffect } from 'react'
import { useSessionStore } from '../stores/session'
import type { CounselStage } from '../lib/types'

const stageLabel: Record<CounselStage, string> = {
  specialist: 'STAGE_01',
  skeptic: 'STAGE_02',
  arbiter: 'STAGE_03',
}

function formatTime(ts: number) {
  return new Date(ts).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatName(name: string) {
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export function DeliberationStream() {
  const stream = useSessionStore((s) => s.stream)
  const status = useSessionStore((s) => s.status)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [stream])

  return (
    <div className="flex-1 flex flex-col h-full bg-surface-panel/20 relative">
      {/* Header */}
      <div className="p-4 border-b border-border-subtle flex justify-between items-center bg-surface/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-accent text-sm">memory</span>
          <h3 className="font-mono text-[10px] font-bold uppercase tracking-widest text-text-secondary">
            LIVE_REASONING_LOG
          </h3>
        </div>
        {status === 'running' && (
          <div className="flex gap-2 items-center bg-orange-50 px-3 py-1 rounded-full border border-orange-200 shadow-sm">
            <div className="w-1.5 h-1.5 rounded-full bg-primary-accent animate-pulse" />
            <span className="text-[10px] font-mono font-bold tracking-widest text-primary-accent">STREAM_ACTIVE</span>
          </div>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-8 font-mono space-y-8">
        {stream.length === 0 && status === 'idle' && (
          <div className="flex flex-col items-center justify-center h-full opacity-60">
            <span className="material-symbols-outlined text-text-secondary text-[40px] mb-4">history_edu</span>
            <p className="text-sm font-semibold text-text-primary">AWAITING_SESSION</p>
            <p className="text-[11px] text-text-secondary mt-2 font-body">Load a report or initiate a live review</p>
          </div>
        )}

        {stream.map((msg) => {
          const isActive = msg.type === 'thinking'
          const label = stageLabel[msg.stage]

          return (
            <div key={msg.id} className="relative group">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-[10px] text-text-secondary bg-surface-card px-2 py-0.5 rounded border border-border-subtle shadow-sm">
                  {formatTime(msg.timestamp)}
                </span>
                <span className={`text-[9px] font-bold tracking-widest px-2 py-0.5 rounded-sm border shadow-sm ${
                  isActive
                    ? 'text-primary-accent bg-orange-50 border-orange-200'
                    : 'text-text-secondary bg-surface-panel border-border-subtle'
                }`}>
                  {label}
                </span>
                <span className={`text-xs font-bold tracking-tight ${isActive ? 'text-text-primary' : 'text-text-secondary'}`}>
                  {formatName(msg.counselName)}
                </span>
                {msg.type === 'result' && (
                  <span className="text-[9px] uppercase tracking-widest px-2 py-0.5 rounded-sm text-emerald-700 bg-emerald-50 border border-emerald-200 shadow-sm">
                    VERDICT
                  </span>
                )}
              </div>
              <div className={`ml-2 pl-5 border-l-[3px] py-1 ${
                isActive
                  ? 'border-primary-accent bg-gradient-to-r from-orange-50/50 to-transparent py-4 rounded-r-lg'
                  : 'border-border-subtle'
              }`}>
                <p className={`text-sm leading-loose whitespace-pre-wrap ${
                  isActive ? 'text-text-primary' : 'text-text-secondary'
                }`}>
                  {msg.content}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
