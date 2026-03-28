import { useState } from 'react'
import { useSessionStore } from '../stores/session'
import type { CorpusChapter } from '../lib/types'

export function CorpusBrowser() {
  const corpusPath = useSessionStore((s) => s.corpusPath)
  const setCorpusPath = useSessionStore((s) => s.setCorpusPath)
  const chapters = useSessionStore((s) => s.chapters)
  const setChapters = useSessionStore((s) => s.setChapters)
  const startSession = useSessionStore((s) => s.startSession)

  const [pathInput, setPathInput] = useState(corpusPath || '')
  const [scanning, setScanning] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(new Set())
  const [launchingRule, setLaunchingRule] = useState<string | null>(null)

  const handleScan = async () => {
    if (!pathInput.trim()) return
    setScanning(true)
    setScanError(null)
    try {
      const res = await fetch('/api/corpus/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ corpus_path: pathInput.trim() }),
      })
      if (!res.ok) {
        const errText = await res.text()
        throw new Error(errText)
      }
      const data = await res.json()
      setCorpusPath(pathInput.trim())
      setChapters(data.chapters || [])
      // Auto-expand the first chapter
      if (data.chapters?.length) {
        setExpandedChapters(new Set([data.chapters[0].number]))
      }
    } catch (err) {
      setScanError(err instanceof Error ? err.message : 'Scan failed')
    } finally {
      setScanning(false)
    }
  }

  const toggleChapter = (chapterNumber: string) => {
    setExpandedChapters((prev) => {
      const next = new Set(prev)
      if (next.has(chapterNumber)) {
        next.delete(chapterNumber)
      } else {
        next.add(chapterNumber)
      }
      return next
    })
  }

  const handleReview = async (ruleNumber: string) => {
    if (!corpusPath) return
    setLaunchingRule(ruleNumber)
    try {
      const res = await fetch('/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rule_number: ruleNumber, corpus_path: corpusPath }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      startSession(data.session_id, `CGST-R${data.rule_number}`)
    } catch (err) {
      console.error('Failed to start review:', err)
      alert('Failed to start review. Make sure the backend is running.')
    } finally {
      setLaunchingRule(null)
    }
  }

  const totalRules = chapters.reduce((sum, ch) => sum + ch.rules.length, 0)

  return (
    <div className="corpus-browser">
      {/* Scan Bar */}
      <div className="corpus-scan-bar">
        <div className="corpus-scan-inner">
          <label className="corpus-scan-label">CORPUS PATH</label>
          <input
            type="text"
            className="corpus-scan-input"
            value={pathInput}
            onChange={(e) => setPathInput(e.target.value)}
            placeholder="Absolute path to extracted corpus..."
            onKeyDown={(e) => e.key === 'Enter' && handleScan()}
          />
          <button
            className="corpus-scan-btn"
            onClick={handleScan}
            disabled={scanning || !pathInput.trim()}
          >
            {scanning ? (
              <>
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>progress_activity</span>
                Scanning...
              </>
            ) : (
              <>
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>radar</span>
                Scan
              </>
            )}
          </button>
        </div>
        {scanError && (
          <div className="corpus-scan-error">
            <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>error</span>
            {scanError}
          </div>
        )}
      </div>

      {/* Results */}
      {chapters.length > 0 ? (
        <>
          <div className="corpus-summary">
            <span>{chapters.length} chapters</span>
            <span className="corpus-summary-dot" />
            <span>{totalRules} rules</span>
          </div>

          <div className="corpus-chapters">
            {chapters.map((ch: CorpusChapter) => {
              const isExpanded = expandedChapters.has(ch.number)
              return (
                <div key={ch.dir_name} className="chapter-card">
                  <button
                    className="chapter-header"
                    onClick={() => toggleChapter(ch.number)}
                  >
                    <div className="chapter-header-left">
                      <span className="chapter-number">Ch. {ch.number}</span>
                      <span className="chapter-title">{ch.title}</span>
                    </div>
                    <div className="chapter-header-right">
                      <span className="chapter-rule-count">{ch.rules.length} rules</span>
                      <span
                        className="material-symbols-outlined chapter-chevron"
                        style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}
                      >
                        expand_more
                      </span>
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="chapter-rules">
                      <div className="rule-row rule-row-header">
                        <span className="rule-col-num">Rule</span>
                        <span className="rule-col-title">Title</span>
                        <span className="rule-col-meta">Nodes</span>
                        <span className="rule-col-meta">Amendments</span>
                        <span className="rule-col-action" />
                      </div>
                      {ch.rules.map((rule) => (
                        <div key={rule.rule_number} className="rule-row">
                          <span className="rule-col-num">{rule.rule_number}</span>
                          <span className="rule-col-title">{rule.title}</span>
                          <span className="rule-col-meta">{rule.node_count}</span>
                          <span className="rule-col-meta">{rule.amendment_count}</span>
                          <span className="rule-col-action">
                            <button
                              className="rule-review-btn"
                              onClick={() => handleReview(rule.rule_number)}
                              disabled={launchingRule === rule.rule_number}
                            >
                              {launchingRule === rule.rule_number ? 'Launching...' : 'Review'}
                            </button>
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      ) : !scanning ? (
        <div className="corpus-empty">
          <span className="material-symbols-outlined" style={{ fontSize: '40px' }}>folder_open</span>
          <h4>No corpus loaded</h4>
          <p>Enter a path above and hit Scan to browse extracted chapters and rules.</p>
        </div>
      ) : null}
    </div>
  )
}
