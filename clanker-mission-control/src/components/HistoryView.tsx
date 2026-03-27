import { useState, useEffect } from 'react'
import { useSessionStore } from '../stores/session'
import type { RuleReport } from '../lib/types'

interface HistoryEntry {
  id: string
  session_id: string
  timestamp: number
  report: RuleReport
}

export function HistoryView() {
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const loadReport = useSessionStore((s) => s.loadReport)

  useEffect(() => {
    fetch('http://localhost:8420/api/history')
      .then(res => res.json())
      .then(data => {
        setHistory(data.history || [])
        setLoading(false)
      })
      .catch(err => {
        console.error("Failed to load history", err)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="history-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="empty-state">
          <span className="material-symbols-outlined animate-spin-slow" style={{ fontSize: '48px', color: 'var(--accent-secondary)' }}>autorenew</span>
          <h4>LOADING_ARCHIVES</h4>
        </div>
      </div>
    )
  }

  return (
    <div className="history-container">
      <div className="history-header">
        <h2 className="history-title">
          <span className="material-symbols-outlined" style={{ color: 'var(--accent-secondary)' }}>history</span>
          HISTORICAL_LOGS
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Review past extractions, verdicts, and issue reports.</p>
      </div>

      {history.length === 0 ? (
        <div className="empty-state">
          <span className="material-symbols-outlined" style={{ fontSize: '48px' }}>inbox</span>
          <h4>NO_RECORDS_FOUND</h4>
          <p>Run a live review to populate the history.</p>
        </div>
      ) : (
        <div className="history-grid">
          {history.map(entry => {
            const date = new Date(entry.timestamp).toLocaleString('en-US', {
              month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
            })
            
            const r = entry.report
            const confirmed = r.confirmed_issues?.length || 0
            const accepted = r.accepted_artifacts?.length || 0
            
            const isErr = r.status === 'issues_found'
            const isOk = r.status === 'clean'
            const isWarn = r.status === 'needs_manual_review'
            const statusColor = isErr ? 'var(--status-error)' : isOk ? 'var(--status-success)' : isWarn ? 'var(--status-warning)' : 'var(--accent-secondary)'
            const statusBg = isErr ? 'var(--status-error-bg)' : isOk ? 'var(--status-success-bg)' : isWarn ? 'var(--status-warning-bg)' : 'var(--accent-secondary-dim)'

            return (
              <div key={entry.id} className="history-card" onClick={() => loadReport(entry.report)}>
                <div className="history-meta">
                  <span className="history-date">
                    <span className="material-symbols-outlined" style={{ fontSize: '14px', marginRight: '4px', verticalAlign: 'text-bottom' }}>calendar_today</span>
                    {date}
                  </span>
                  <span style={{
                    fontSize: '0.6rem',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 800,
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    padding: '2px 8px',
                    borderRadius: 'var(--border-radius-pill)',
                    color: statusColor,
                    backgroundColor: statusBg,
                    border: `1px solid ${statusColor}`
                  }}>
                    {r.status.replace(/_/g, ' ')}
                  </span>
                </div>
                
                <h3 className="history-rule">{r.rule_id}</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {r.summary}
                </p>

                <div className="history-stats">
                  <div className="history-stat" style={{ color: 'var(--status-error)' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>error</span>
                    {confirmed} ISSUES
                  </div>
                  <div className="history-stat" style={{ color: 'var(--status-success)' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>check_circle</span>
                    {accepted} ACCEPTED
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
