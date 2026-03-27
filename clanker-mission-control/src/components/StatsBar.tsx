import { useSessionStore } from '../stores/session'

interface StatsBarProps {
  ruleId: string | null
}

export function StatsBar({ ruleId }: StatsBarProps) {
  const stats = useSessionStore((s) => s.stats)
  
  const elapsed = stats.startedAt ? Math.floor(((stats.completedAt || Date.now()) - stats.startedAt) / 1000) : 0
  const duration = elapsed > 0 ? `${elapsed}s` : '--'
  const tokens = stats.totalTokens > 0 ? stats.totalTokens.toLocaleString() : '--'
  const cost = stats.totalTokens > 0 ? `$${(stats.totalTokens * 0.000002).toFixed(2)}` : '--'

  return (
    <section className="stats-bar">
      <Stat icon="token" label="TOKEN_COUNT" value={tokens} theme="indigo" />
      <div style={{ width: '1px', height: '32px', background: 'var(--border-subtle)' }} />
      <Stat icon="payments" label="COST_USD" value={cost} theme="emerald" />
      <div style={{ width: '1px', height: '32px', background: 'var(--border-subtle)' }} />
      <Stat icon="timer" label="DURATION" value={duration} theme="amber" />
      
      {ruleId && (
        <div className="rule-badge">
          <span className="material-symbols-outlined">policy</span>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span className="label">RULE_ID</span>
            <span className="value">{ruleId}</span>
          </div>
        </div>
      )}
    </section>
  )
}

function Stat({ icon, label, value, theme }: { icon: string; label: string; value: string; theme: string }) {
  return (
    <div className="stat-item">
      <div className={`stat-icon ${theme}`}>
        <span className="material-symbols-outlined">{icon}</span>
      </div>
      <div className="stat-details">
        <span className="stat-label">{label}</span>
        <span className="stat-value">{value}</span>
      </div>
    </div>
  )
}
