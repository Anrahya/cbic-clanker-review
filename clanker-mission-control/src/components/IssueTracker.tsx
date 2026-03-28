import { useSessionStore } from '../stores/session'
import type { CandidateIssue, FinalDisposition } from '../lib/types'
import { useState } from 'react'

const dispStyles: Record<FinalDisposition, { label: string; icon: string; className: string }> = {
  confirmed_issue:     { label: 'CONFIRMED',     icon: 'error',           className: 'status-error' },
  acceptable_artifact: { label: 'ACCEPTED',      icon: 'check_circle',    className: 'status-success' },
  manual_review:       { label: 'MANUAL_REVIEW', icon: 'visibility',      className: 'status-warning' },
  rejected:            { label: 'REJECTED',      icon: 'cancel',          className: 'status-inactive' },
}

function IssueCard({ issue, onClick }: { issue: CandidateIssue; onClick: () => void }) {
  return (
    <button onClick={onClick} className="issue-card">
      <div className="card-header">
        {issue.severity && <span className={`sev-dot sev-${issue.severity}`} />}
        <span className="node-ref">
          {issue.node_id || issue.issue_id}
        </span>
      </div>
      <div className="card-title">
        {issue.title || 'Untitled Issue'}
      </div>
    </button>
  )
}

function IssueDetail({ issue, onClose }: { issue: CandidateIssue; onClose: () => void }) {
  const disp = issue.final_disposition ? dispStyles[issue.final_disposition] : null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <div className="modal-meta">
              <span className="node-ref" style={{ fontSize: '0.75rem', padding: '4px 10px' }}>
                {issue.issue_id}
              </span>
              {disp && (
                <span className={`disp-badge ${disp.className}`} style={{ 
                  color: `var(--${disp.className})`, 
                  backgroundColor: `var(--${disp.className}-bg)`, 
                  borderColor: `rgba(var(--${disp.className}), 0.2)` 
                }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>{disp.icon}</span>
                  {disp.label}
                </span>
              )}
            </div>
            <h3 className="modal-title">{issue.title}</h3>
          </div>
          <button onClick={onClose} className="modal-close">
            <span className="material-symbols-outlined" style={{ fontSize: '28px' }}>close</span>
          </button>
        </div>

        {/* Content */}
        <div className="modal-body">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
            <div className="field-group">
              <span className="field-label">NODE REFERENCE</span>
              <div className="node-ref" style={{ display: 'inline-flex', padding: '6px 12px', fontSize: '0.8rem', width: 'fit-content' }}>
                {issue.node_id || 'N/A'}
              </div>
            </div>
            {issue.severity && (
              <div className="field-group">
                <span className="field-label">SEVERITY</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px' }}>
                  <span className={`sev-dot sev-${issue.severity}`} style={{ width: '12px', height: '12px' }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', fontWeight: 800, textTransform: 'uppercase' }}>
                    {issue.severity}
                  </span>
                </div>
              </div>
            )}
          </div>

          {issue.problem && (
            <div className="field-group">
              <span className="field-label">PROBLEM DESCRIPTION</span>
              <div className="field-content problem">{issue.problem}</div>
            </div>
          )}

          {issue.evidence_refs.length > 0 && (
            <div className="field-group">
              <span className="field-label">EVIDENCE LOGS</span>
              <div>
                {issue.evidence_refs.map((ref, i) => (
                  <div key={i} className="evidence-box">
                    {ref}
                  </div>
                ))}
              </div>
            </div>
          )}

          {issue.recommended_fix && (
            <div className="field-group">
              <span className="field-label">RECOMMENDED FIX</span>
              <div className="field-content fix">{issue.recommended_fix}</div>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', borderTop: '1px solid var(--border-subtle)', paddingTop: '32px' }}>
            {issue.supporting_counsel.length > 0 && (
              <div className="field-group">
                <span className="field-label">SUPPORTING COUNSEL</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {issue.supporting_counsel.map(c => (
                    <span key={c} className="node-ref" style={{ color: 'var(--accent-secondary)', background: 'var(--accent-secondary-dim)', borderColor: 'var(--accent-secondary)' }}>
                      {c.replace(/_/g, ' ').toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {issue.metadata?.max_confidence != null && (
              <div className="field-group">
                <span className="field-label">SYSTEM CONFIDENCE</span>
                <div style={{ fontFamily: 'var(--font-headline)', fontSize: '2.5rem', fontWeight: 900, color: 'var(--text-primary)', lineHeight: 1 }}>
                  {((issue.metadata.max_confidence as number) * 100).toFixed(0)}
                  <span style={{ fontSize: '1.2rem', color: 'var(--text-secondary)' }}>%</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function IssueTracker() {
  const report = useSessionStore((s) => s.report)
  const [selectedIssue, setSelectedIssue] = useState<CandidateIssue | null>(null)

  const columns: { key: FinalDisposition; issues: CandidateIssue[] }[] = [
    { key: 'confirmed_issue', issues: report?.confirmed_issues || [] },
    { key: 'acceptable_artifact', issues: report?.accepted_artifacts || [] },
    { key: 'manual_review', issues: report?.manual_review_issues || [] },
    { key: 'rejected', issues: report?.rejected_issues || [] },
  ]

  const nonEmpty = columns.filter(c => c.issues.length > 0)
  if (!report) return null

  return (
    <>
      <div className="issue-tracker-container">
        {nonEmpty.map(({ key, issues }) => {
          const cfg = dispStyles[key]
          const colorVar = cfg.className === 'status-inactive' ? 'var(--text-secondary)' : `var(--${cfg.className})`
          
          return (
            <div key={key} className="issue-column">
              <div className="col-header">
                <div className="col-title" style={{ color: colorVar }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>{cfg.icon}</span>
                  {cfg.label}
                </div>
                <div className="col-count" style={{ color: colorVar, borderColor: colorVar }}>
                  {issues.length}
                </div>
              </div>
              <div className="col-cards">
                {issues.map(issue => (
                  <IssueCard key={issue.issue_id} issue={issue} onClick={() => setSelectedIssue(issue)} />
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {selectedIssue && <IssueDetail issue={selectedIssue} onClose={() => setSelectedIssue(null)} />}
    </>
  )
}
