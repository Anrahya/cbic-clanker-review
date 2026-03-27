import { useState, useRef } from 'react'
import { CouncilRoster } from './components/CouncilRoster'
import { DeliberationStream } from './components/DeliberationStream'
import { IssueTracker } from './components/IssueTracker'
import { HistoryView } from './components/HistoryView'
import { StatsBar } from './components/StatsBar'
import { useSessionStore } from './stores/session'
import { useWebSocket } from './hooks/useWebSocket'
import type { RuleReport } from './lib/types'

function App() {
  const loadReport = useSessionStore((s) => s.loadReport)
  const startSession = useSessionStore((s) => s.startSession)
  const sessionId = useSessionStore((s) => s.sessionId)
  const status = useSessionStore((s) => s.status)
  const activeView = useSessionStore((s) => s.activeView)
  const setActiveView = useSessionStore((s) => s.setActiveView)
  const report = useSessionStore((s) => s.report)
  const ruleId = useSessionStore((s) => s.ruleId)
  const errorMsg = useSessionStore((s) => s.error)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [ruleInput, setRuleInput] = useState('19')
  const [corpusInput, setCorpusInput] = useState('D:\\Agents\\claude-code\\cbic-gst-scraper\\data\\gst_rules\\cgst_rules_2017')
  
  // Wire up the websocket hook
  useWebSocket(sessionId)

  const handleLoadReport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const text = await file.text()
      const data = JSON.parse(text) as RuleReport
      loadReport(data)
    } catch {
      console.error('Failed to parse report JSON')
    }
  }

  const handleStartReview = async () => {
    if (!ruleInput.trim() || !corpusInput.trim()) return
    try {
      const ruleNum = ruleInput.trim()
      const res = await fetch('http://localhost:8420/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rule_number: ruleNum, corpus_path: corpusInput.trim() })
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      startSession(data.session_id, `CGST-R${data.rule_number}`)
    } catch (err) {
      console.error("Failed to start review:", err)
      alert("Failed to connect to backend server. Make sure `python -m uvicorn clanker_zone.server:app --port 8420` is running.")
    }
  }

  return (
    <div className="app-shell">
      <div className="app-background" />

      {/* ═══ TOP NAV ═══ */}
      <header className="top-nav">
        <div className="brand-title">
          <span className="material-symbols-outlined">public</span>
          CLANKER_ZONE
          
          <div style={{ marginLeft: '16px', display: 'flex', gap: '20px' }}>
            {status === 'running' && (
              <div className="status-indicator running">
                <span className="status-dot running animate-pulse-orange" />
                SYSTEM_ACTIVE
              </div>
            )}
            {status === 'complete' && (
              <div className="status-indicator complete">
                <span className="status-dot complete" />
                SYSTEM_STABLE
              </div>
            )}
            {status === 'idle' && (
              <div className="status-indicator idle">STANDBY</div>
            )}
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button className="btn-ghost">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button className="btn-ghost">
            <span className="material-symbols-outlined">settings</span>
          </button>
          <div style={{ width: '1px', height: '16px', background: 'var(--border-subtle)' }} />
          
          <input ref={fileInputRef} type="file" accept=".json" onChange={handleLoadReport} style={{ display: 'none' }} />
          <button onClick={() => fileInputRef.current?.click()} className="btn-ghost">
            LOAD JSON
          </button>
          
          <div className="command-bar">
            <div className="command-label">CORPUS</div>
            <input 
              type="text" 
              value={corpusInput} 
              onChange={e => setCorpusInput(e.target.value)}
              disabled={status === 'running'}
              className="command-input mono"
              placeholder="Absolute path to corpus"
            />
            <div className="command-label">RULE</div>
            <input 
              type="text" 
              value={ruleInput} 
              onChange={e => setRuleInput(e.target.value)}
              disabled={status === 'running'}
              className="command-input bold"
              placeholder="e.g. 19"
            />
            <button
              onClick={handleStartReview}
              disabled={status === 'running' || !ruleInput.trim() || !corpusInput.trim()}
              className="btn-primary"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>bolt</span>
              LIVE
            </button>
          </div>
        </div>
      </header>

      <div className="layout-body">
        {/* ═══ SIDE NAV ═══ */}
        <aside className="side-nav">
          <div className="operator-card">
            <div className="operator-avatar">
              <span className="material-symbols-outlined">engineering</span>
            </div>
            <div className="operator-details">
              <span className="operator-name">OPERATOR_01</span>
              <span className="operator-role">SOVEREIGN</span>
            </div>
          </div>
          
          <nav className="nav-menu">
            <div className="nav-label">TERMINAL VIEWS</div>
            <div className={`nav-item ${activeView === 'mission_control' ? 'active' : ''}`} onClick={() => setActiveView('mission_control')}>
              <span className="material-symbols-outlined">dashboard</span>
              <span>MISSION_CONTROL</span>
            </div>
            <div className={`nav-item ${activeView === 'history' ? 'active' : ''}`} onClick={() => setActiveView('history')}>
              <span className="material-symbols-outlined">history</span>
              <span>HISTORY_LOGS</span>
            </div>
          </nav>
        </aside>

        {/* ═══ MAIN CONTENT ═══ */}
        <main className="workspace">
          {activeView === 'mission_control' ? (
            <>
              <StatsBar ruleId={ruleId} />

              <div className="panels-container">
                {/* Intelligence Pipeline */}
                <section className="glass-panel roster-panel">
                  <div className="panel-header">
                    <div className="panel-title">
                      <span className="material-symbols-outlined">hub</span>
                      INTELLIGENCE_PIPELINE
                    </div>
                  </div>
                  <div className="roster-content">
                    <CouncilRoster />
                  </div>
                </section>

                {/* Center panel */}
                <section className="glass-panel feed-panel">
                  {report ? (
                    <>
                      <div className="panel-header">
                        <div className="panel-title">
                          <span className="material-symbols-outlined">analytics</span>
                          REPORT_VIEW
                        </div>
                        <StatusBadge status={report.status} />
                      </div>
                      <div className="report-header">
                        <h2 className="report-rule">{report.rule_id}</h2>
                        <p className="report-summary">{report.summary}</p>
                      </div>
                      <div style={{ flex: 1, padding: '32px', overflowY: 'hidden', height: '100%' }}>
                        <IssueTracker />
                      </div>
                    </>
                  ) : (
                    <DeliberationStream />
                  )}
                </section>
              </div>
            </>
          ) : (
            <HistoryView />
          )}
        </main>
      </div>

      {/* ═══ ERROR BANNER ═══ */}
      {status === 'error' && errorMsg && (
        <div className="error-banner">
          <span className="material-symbols-outlined">error</span>
          <div>
            <h3>SESSION ERROR</h3>
            <p>{errorMsg}</p>
          </div>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const isErr = status === 'issues_found'
  const isOk = status === 'clean'
  const isWarn = status === 'needs_manual_review'
  const color = isErr ? 'var(--status-error)' : isOk ? 'var(--status-success)' : isWarn ? 'var(--status-warning)' : 'var(--accent-secondary)'
  const bg = isErr ? 'var(--status-error-bg)' : isOk ? 'var(--status-success-bg)' : isWarn ? 'var(--status-warning-bg)' : 'var(--accent-secondary-dim)'
  
  return (
    <span style={{
      fontSize: '0.65rem',
      fontFamily: 'var(--font-mono)',
      fontWeight: 800,
      letterSpacing: '0.1em',
      textTransform: 'uppercase',
      padding: '4px 12px',
      borderRadius: 'var(--border-radius-pill)',
      color: color,
      backgroundColor: bg,
      border: `1px solid ${color}`
    }}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}

export default App
