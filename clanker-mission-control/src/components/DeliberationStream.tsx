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
    <>
      <div className="panel-header">
        <div className="panel-title">
          <span className="material-symbols-outlined" style={{ color: 'var(--accent-secondary)' }}>memory</span>
          LIVE_REASONING_LOG
        </div>
        {status === 'running' && (
          <div className="status-indicator running" style={{ background: 'var(--bg-surface-elevated)', padding: '4px 12px', border: '1px solid var(--accent-primary)', borderRadius: 'var(--border-radius-pill)' }}>
            <span className="status-dot running animate-pulse-orange" />
            <span style={{ color: 'var(--accent-primary)' }}>STREAM_ACTIVE</span>
          </div>
        )}
      </div>

      <div ref={scrollRef} className="feed-content">
        {stream.length === 0 && status === 'idle' && (
          <div className="empty-state">
            <span className="material-symbols-outlined">history_edu</span>
            <h4>AWAITING_SESSION</h4>
            <p>Load a report or initiate a live review</p>
          </div>
        )}

        {stream.map((msg) => {
          const isActive = msg.type === 'thinking'
          const label = stageLabel[msg.stage]

          return (
            <div key={msg.id} className="stream-message">
              <div className="msg-header">
                <span className="msg-time">{formatTime(msg.timestamp)}</span>
                <span className={`msg-stage ${isActive ? 'active' : 'inactive'}`}>
                  {label}
                </span>
                <span className={`msg-author ${isActive ? 'active' : 'inactive'}`}>
                  {formatName(msg.counselName)}
                </span>
                {msg.type === 'result' && (
                  <span style={{
                    fontSize: '0.6rem',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    letterSpacing: '0.15em',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: 'var(--status-success-bg)',
                    color: 'var(--status-success)',
                    border: '1px solid var(--status-success)'
                  }}>VERDICT</span>
                )}
              </div>
              <div className={`msg-body ${isActive ? 'active' : 'inactive'}`}>
                {msg.content}
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}
