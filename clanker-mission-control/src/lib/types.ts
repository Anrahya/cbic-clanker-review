/* Types mirroring the Python clanker_zone models */

export type Severity = 'critical' | 'major' | 'moderate' | 'minor'
export type FinalDisposition = 'confirmed_issue' | 'acceptable_artifact' | 'manual_review' | 'rejected'
export type ReportStatus = 'clean' | 'issues_found' | 'accepted_with_artifacts' | 'needs_manual_review'
export type CounselStage = 'specialist' | 'skeptic' | 'arbiter'

export interface CandidateIssue {
  issue_id: string
  signature: string
  dossier_id: string
  node_id: string | null
  category: string | null
  severity: Severity | null
  title: string | null
  problem: string | null
  evidence_refs: string[]
  recommended_fix: string | null
  supporting_task_ids: string[]
  supporting_counsel: string[]
  metadata: Record<string, unknown>
  final_disposition: FinalDisposition | null
}

export interface RuleReport {
  rule_id: string
  status: ReportStatus
  confirmed_issues: CandidateIssue[]
  accepted_artifacts: CandidateIssue[]
  manual_review_issues: CandidateIssue[]
  rejected_issues: CandidateIssue[]
  summary: string
  diagnostics: Record<string, unknown>
}

export interface CounselStatus {
  name: string
  displayName: string
  stage: CounselStage
  status: 'waiting' | 'active' | 'complete' | 'error'
  tokenCount: number
  startedAt: number | null
  completedAt: number | null
}

export interface StreamEvent {
  type: 'counsel_start' | 'counsel_chunk' | 'counsel_result' | 'stage_complete' | 'report_complete' | 'error'
  timestamp: number
  counsel_name?: string
  stage?: CounselStage
  content?: string
  judgment?: Record<string, unknown>
  report?: RuleReport
  token_count?: number
  error?: string
}

export interface SessionMeta {
  session_id: string
  rule_id: string
  rule_number: string
  started_at: number
  completed_at: number | null
  status: 'running' | 'complete' | 'error'
}
