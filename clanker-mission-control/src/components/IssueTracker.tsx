import { useSessionStore } from '../stores/session'
import type { CandidateIssue, FinalDisposition, Severity } from '../lib/types'
import { useState } from 'react'

const dispStyles: Record<FinalDisposition, { label: string; icon: string; color: string; bg: string; border: string }> = {
  confirmed_issue:     { label: 'CONFIRMED',     icon: 'error',           color: 'text-red-700',       bg: 'bg-red-50',       border: 'border-red-200' },
  acceptable_artifact: { label: 'ACCEPTED',      icon: 'check_circle',    color: 'text-emerald-700',   bg: 'bg-emerald-50',   border: 'border-emerald-200' },
  manual_review:       { label: 'MANUAL_REVIEW', icon: 'visibility',      color: 'text-amber-700',     bg: 'bg-amber-50',     border: 'border-amber-200' },
  rejected:            { label: 'REJECTED',      icon: 'cancel',          color: 'text-text-secondary',bg: 'bg-surface-panel',border: 'border-border-subtle' },
}

const sevDots: Record<Severity, string> = {
  critical: 'bg-red-500',
  major:    'bg-orange-500',
  moderate: 'bg-amber-500',
  minor:    'bg-stone-400',
}

function IssueCard({ issue, onClick }: { issue: CandidateIssue; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 border border-border-subtle bg-surface-card hover:border-primary-accent/50 hover:shadow-soft 
        transition-all cursor-pointer group rounded-xl flex flex-col gap-3 shadow-sm"
    >
      <div className="flex items-center gap-2">
        {issue.severity && <span className={`w-2.5 h-2.5 rounded-full ${sevDots[issue.severity]} shadow-sm`} />}
        <span className="text-[10px] font-mono text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100 font-bold tracking-tight">
          {issue.node_id || issue.issue_id}
        </span>
      </div>
      <div className="text-sm font-semibold text-text-primary leading-snug line-clamp-3 group-hover:text-primary-accent transition-colors font-body">
        {issue.title || 'Untitled Issue'}
      </div>
    </button>
  )
}

function IssueDetail({ issue, onClose }: { issue: CandidateIssue; onClose: () => void }) {
  const disp = issue.final_disposition ? dispStyles[issue.final_disposition] : null

  return (
    <div className="fixed inset-0 z-[100] flex justify-end">
      <div className="absolute inset-0 bg-stone-900/20 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-2xl bg-surface border-l border-border-subtle overflow-y-auto shadow-2xl flex flex-col animate-slide-in">
        {/* Header */}
        <div className="p-8 border-b border-border-subtle bg-surface-card flex justify-between items-start sticky top-0 z-10 shadow-sm">
          <div className="pr-6">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-[10px] font-mono bg-surface-panel text-text-secondary px-2.5 py-1 rounded border border-border-subtle font-bold">
                {issue.issue_id}
              </span>
              {disp && (
                <span className={`flex items-center gap-1.5 text-[10px] font-mono font-bold px-3 py-1 rounded-full border shadow-sm ${disp.color} ${disp.bg} ${disp.border}`}>
                  <span className="material-symbols-outlined text-[14px]">{disp.icon}</span>
                  {disp.label}
                </span>
              )}
            </div>
            <h3 className="text-2xl font-headline font-bold tracking-tight text-text-primary leading-snug">{issue.title}</h3>
          </div>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary transition-colors bg-surface-panel hover:bg-border-subtle p-2.5 rounded-full">
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-8 space-y-10 flex-1 bg-surface">
          <div className="grid grid-cols-2 gap-8">
            <Field label="NODE REFERENCE">
              <div className="text-sm font-mono font-bold text-indigo-800 bg-indigo-50 border border-indigo-200 px-3 py-1.5 rounded-md inline-block shadow-sm">
                {issue.node_id || 'N/A'}
              </div>
            </Field>
            {issue.severity && (
              <Field label="SEVERITY">
                <div className="flex items-center gap-2 mt-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${sevDots[issue.severity]} shadow-sm`} />
                  <span className="text-sm font-mono uppercase text-text-primary font-bold tracking-wide">{issue.severity}</span>
                </div>
              </Field>
            )}
          </div>

          {issue.problem && (
            <Field label="PROBLEM DESCRIPTION">
              <div className="text-[15px] font-body text-text-primary leading-relaxed bg-surface-card p-5 rounded-lg border border-border-subtle shadow-sm selection:bg-orange-200">
                {issue.problem}
              </div>
            </Field>
          )}

          {issue.evidence_refs.length > 0 && (
            <Field label="EVIDENCE">
              <div className="space-y-3">
                {issue.evidence_refs.map((ref, i) => (
                  <div key={i} className="text-[13px] font-mono font-medium text-emerald-800 bg-emerald-50 border border-emerald-200 p-4 rounded-lg shadow-sm leading-relaxed">
                    {ref}
                  </div>
                ))}
              </div>
            </Field>
          )}

          {issue.recommended_fix && (
            <Field label="RECOMMENDED FIX">
              <div className="text-[15px] font-body text-amber-900 leading-relaxed bg-[#fffbeb] p-5 rounded-lg border border-amber-200 shadow-sm">
                {issue.recommended_fix}
              </div>
            </Field>
          )}

          <div className="grid grid-cols-2 gap-8 pt-8 border-t border-border-subtle">
            {issue.supporting_counsel.length > 0 && (
              <Field label="SUPPORTING COUNSEL">
                <div className="flex gap-2 flex-wrap mt-2">
                  {issue.supporting_counsel.map(c => (
                    <span key={c} className="text-[10px] font-mono font-bold tracking-widest px-2.5 py-1 rounded-md text-primary-accent bg-orange-50 border border-orange-200 shadow-sm">
                      {c.replace(/_/g, ' ').toUpperCase()}
                    </span>
                  ))}
                </div>
              </Field>
            )}
            {issue.metadata?.max_confidence != null && (
              <Field label="CONFIDENCE">
                <div className="text-3xl font-headline font-black text-text-primary mt-1 tracking-tighter">
                  {((issue.metadata.max_confidence as number) * 100).toFixed(0)}<span className="text-xl text-text-secondary ml-0.5">%</span>
                </div>
              </Field>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span className="w-1.5 h-1.5 rounded-full bg-border-subtle" />
        <span className="text-[10px] font-mono tracking-widest uppercase text-text-secondary font-bold">{label}</span>
      </div>
      {children}
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
      <div className="flex gap-8 h-full overflow-x-auto pb-4 px-2">
        {nonEmpty.map(({ key, issues }) => {
          const cfg = dispStyles[key]
          return (
            <div key={key} className="flex flex-col flex-1 min-w-[300px] max-w-[420px]">
              <div className="flex items-center justify-between mb-5 border-b-2 border-border-subtle pb-3">
                <div className="flex items-center gap-2.5">
                  <span className={`material-symbols-outlined text-[18px] ${cfg.color}`}>{cfg.icon}</span>
                  <span className={`text-xs font-mono font-bold tracking-widest ${cfg.color}`}>
                    {cfg.label}
                  </span>
                </div>
                <span className="text-[11px] font-mono font-bold text-text-primary bg-surface-card border border-border-subtle px-2.5 py-0.5 rounded-lg shadow-sm">
                  {issues.length}
                </span>
              </div>
              <div className="space-y-4 overflow-y-auto flex-1 pr-2">
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
