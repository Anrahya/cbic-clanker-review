import { useState, useRef } from 'react'
import { CouncilRoster } from './components/CouncilRoster'
import { DeliberationStream } from './components/DeliberationStream'
import { IssueTracker } from './components/IssueTracker'
import { StatsBar } from './components/StatsBar'
import { useSessionStore } from './stores/session'
import { useWebSocket } from './hooks/useWebSocket'
import type { RuleReport } from './lib/types'

function App() {
  const loadReport = useSessionStore((s) => s.loadReport)
  const startSession = useSessionStore((s) => s.startSession)
  const sessionId = useSessionStore((s) => s.sessionId)
  const status = useSessionStore((s) => s.status)
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
      if (!res.ok) {
        throw new Error(await res.text())
      }
      const data = await res.json()
      startSession(data.session_id, `CGST-R${data.rule_number}`)
    } catch (err) {
      console.error("Failed to start review:", err)
      alert("Failed to connect to backend server. Make sure `python -m uvicorn clanker_zone.server:app --port 8420` is running.")
    }
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-surface text-text-primary font-body selection:bg-orange-200 selection:text-orange-900">
      {/* ═══ TOP NAV ═══ */}
      <header className="bg-surface flex justify-between items-center w-full px-8 h-14 border-b border-border-subtle z-50 shrink-0 shadow-sm">
        <div className="flex items-center gap-8">
          <span className="font-headline font-bold text-lg tracking-wider text-text-primary flex items-center gap-2">
            <span className="material-symbols-outlined text-text-secondary text-lg">public</span>
            CLANKER_ZONE
          </span>
          <nav className="hidden md:flex gap-6 border-l border-border-subtle pl-6 h-6 items-center">
            {status === 'running' && (
              <span className="font-headline uppercase tracking-wide text-xs text-primary-accent font-bold flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary-accent pulse-glow" />
                SYSTEM_ACTIVE
              </span>
            )}
            {status === 'complete' && (
              <span className="font-headline uppercase tracking-wide text-xs text-emerald-700 font-bold flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                SYSTEM_STABLE
              </span>
            )}
            {status === 'idle' && (
              <span className="font-headline uppercase tracking-wide text-xs text-text-secondary font-bold">STANDBY</span>
            )}
          </nav>
        </div>
        <div className="flex items-center gap-5">
          <button className="text-text-secondary hover:text-text-primary transition-colors flex items-center">
            <span className="material-symbols-outlined text-[20px]">notifications</span>
          </button>
          <button className="text-text-secondary hover:text-text-primary transition-colors flex items-center">
            <span className="material-symbols-outlined text-[20px]">settings</span>
          </button>
          <div className="w-[1px] h-4 bg-border-subtle" />
          <input ref={fileInputRef} type="file" accept=".json" onChange={handleLoadReport} className="hidden" />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="text-text-secondary font-headline uppercase tracking-wide text-[11px] hover:text-text-primary transition-all cursor-pointer font-bold"
          >
            LOAD JSON
          </button>
          
          <div className="flex items-center bg-surface-panel border border-border-subtle rounded shadow-sm focus-within:border-primary-accent focus-within:ring-1 focus-within:ring-primary-accent transition-all overflow-hidden ml-4">
            <div className="bg-border-subtle/40 px-3 flex items-center border-r border-border-subtle h-full">
              <span className="font-mono text-[10px] font-bold tracking-widest text-text-secondary uppercase">CORPUS</span>
            </div>
            <input 
              type="text" 
              value={corpusInput} 
              onChange={e => setCorpusInput(e.target.value)}
              disabled={status === 'running'}
              className="w-64 bg-transparent border-none text-xs font-mono text-text-primary px-3 py-1.5 focus:ring-0 disabled:opacity-50"
              placeholder="Absolute path to corpus"
            />
            <div className="bg-border-subtle flex items-center w-[1px] h-4 mx-1" />
            <div className="bg-border-subtle/40 px-3 flex items-center border-x border-border-subtle h-full">
              <span className="font-mono text-[10px] font-bold tracking-widest text-text-secondary uppercase">RULE</span>
            </div>
            <input 
              type="text" 
              value={ruleInput} 
              onChange={e => setRuleInput(e.target.value)}
              disabled={status === 'running'}
              className="w-16 bg-transparent border-none text-sm font-headline font-bold text-text-primary px-3 py-1.5 focus:ring-0 disabled:opacity-50"
              placeholder="e.g. 19"
            />
            <button
              onClick={handleStartReview}
              disabled={status === 'running' || !ruleInput.trim() || !corpusInput.trim()}
              className="bg-primary-accent text-white font-headline uppercase tracking-wide text-[11px] px-4 py-1.5 hover:bg-orange-600 disabled:opacity-50 transition-all font-bold flex items-center gap-1.5 h-full"
            >
              <span className="material-symbols-outlined text-[14px]">bolt</span>
              LIVE
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* ═══ SIDE NAV ═══ */}
        <aside className="bg-surface flex flex-col h-full w-[260px] border-r border-border-subtle shrink-0">
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-surface-card border border-border-subtle rounded-full flex items-center justify-center shadow-card text-primary-accent">
                <span className="material-symbols-outlined text-[20px]">engineering</span>
              </div>
              <div className="flex flex-col justify-center">
                <span className="text-text-primary font-bold text-sm leading-tight">OPERATOR_01</span>
                <span className="text-[10px] text-text-secondary font-mono tracking-wider mt-0.5">SOVEREIGN</span>
              </div>
            </div>
          </div>
          
          <nav className="flex-1 px-3 space-y-1 mt-2">
            <div className="font-mono text-[10px] uppercase tracking-widest text-text-secondary mb-3 px-3 font-semibold">Terminal Views</div>
            <NavItem icon="dashboard" label="MISSION_CONTROL" active />
            <NavItem icon="vital_signs" label="AGENT_STATUS" />
            <NavItem icon="memory" label="REASONING_FEED" />
            <NavItem icon="receipt_long" label="REPORT_VIEW" />
          </nav>
        </aside>

        {/* ═══ MAIN CONTENT ═══ */}
        <main className="flex-1 flex flex-col overflow-hidden bg-surface-panel/50 grid-bg">
          <StatsBar ruleId={ruleId} />

          <div className="flex-1 flex overflow-hidden p-6 gap-6">
            {/* Intelligence Pipeline */}
            <section className="w-80 flex flex-col shrink-0">
              <div className="bg-surface-card border border-border-subtle rounded-xl flex flex-col h-full shadow-card overflow-hidden">
                <div className="p-4 border-b border-border-subtle bg-surface/50">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-text-secondary text-sm">hub</span>
                    <h3 className="font-mono text-[10px] font-bold uppercase tracking-widest text-text-secondary">
                      INTELLIGENCE_PIPELINE
                    </h3>
                  </div>
                </div>
                <CouncilRoster />
              </div>
            </section>

            {/* Center panel */}
            <section className="flex-1 flex flex-col min-w-0">
              <div className="bg-surface-card border border-border-subtle rounded-xl flex flex-col h-full shadow-card overflow-hidden">
                {report ? (
                  <>
                    <div className="p-4 border-b border-border-subtle flex justify-between items-center bg-surface/50">
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-text-secondary text-sm">analytics</span>
                        <h3 className="font-mono text-[10px] font-bold uppercase tracking-widest text-text-secondary">REPORT_VIEW</h3>
                      </div>
                      <StatusBadge status={report.status} />
                    </div>
                    <div className="p-8 border-b border-border-subtle bg-surface-panel/30">
                      <h2 className="font-headline text-3xl font-bold tracking-tight text-text-primary">{report.rule_id}</h2>
                      <p className="text-sm text-text-secondary mt-3 leading-relaxed max-w-2xl">{report.summary}</p>
                    </div>
                    <div className="flex-1 overflow-auto p-8 bg-surface/30">
                      <IssueTracker />
                    </div>
                  </>
                ) : (
                  <DeliberationStream />
                )}
              </div>
            </section>
          </div>
        </main>
      </div>

      {/* ═══ ERROR BANNER ═══ */}
      {status === 'error' && errorMsg && (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 max-w-lg w-full z-50 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="bg-red-50 border border-red-200 text-red-900 px-6 py-4 shadow-xl flex items-center gap-4">
            <span className="material-symbols-outlined text-red-600">error</span>
            <div className="flex-1">
              <h3 className="font-headline font-bold text-sm tracking-wide mb-1">SESSION ERROR</h3>
              <p className="font-mono text-xs">{errorMsg}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function NavItem({ icon, label, active }: { icon: string; label: string; active?: boolean }) {
  return (
    <div className={`px-3 py-2.5 rounded-md flex items-center gap-3 cursor-pointer transition-colors font-medium ${
      active
        ? 'text-primary-accent bg-orange-50 border-l-[3px] border-primary-accent pl-2.5 shadow-sm'
        : 'text-text-secondary hover:text-text-primary hover:bg-surface-panel border-l-[3px] border-transparent pl-2.5'
    }`}>
      <span className="material-symbols-outlined text-[18px]">{icon}</span>
      <span className="font-mono uppercase text-[11px] tracking-widest">{label}</span>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    clean: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    issues_found: 'text-red-700 bg-red-50 border-red-200',
    accepted_with_artifacts: 'text-sky-700 bg-sky-50 border-sky-200',
    needs_manual_review: 'text-amber-700 bg-amber-50 border-amber-200',
  }
  return (
    <span className={`text-[10px] font-mono font-bold uppercase px-3 py-1 rounded-full border ${styles[status] || 'text-text-secondary border-border-subtle'}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}

export default App
