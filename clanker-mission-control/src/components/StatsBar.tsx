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
    <section className="h-20 border-b border-border-subtle flex items-center px-10 gap-10 bg-surface-card shrink-0 shadow-soft z-10 relative">
      <div className="flex items-center gap-16">
        <Stat icon="token" label="TOKEN_COUNT" value={tokens} color="text-indigo-600" bg="bg-indigo-50" />
        <div className="h-8 w-[1px] bg-border-subtle" />
        <Stat icon="payments" label="COST_USD" value={cost} color="text-emerald-600" bg="bg-emerald-50" />
        <div className="h-8 w-[1px] bg-border-subtle" />
        <Stat icon="timer" label="DURATION" value={duration} color="text-amber-600" bg="bg-amber-50" />
      </div>
      
      {ruleId && (
        <div className="ml-auto flex items-center gap-4 bg-surface-panel px-5 py-2.5 rounded-lg border border-border-subtle shadow-inner">
          <span className="material-symbols-outlined text-[20px] text-text-secondary">policy</span>
          <div className="flex flex-col">
            <span className="text-[9px] text-text-secondary uppercase font-mono tracking-widest font-semibold mb-0.5">RULE_ID</span>
            <span className="text-[15px] font-headline font-bold text-text-primary leading-none">{ruleId}</span>
          </div>
        </div>
      )}
    </section>
  )
}

function Stat({ icon, label, value, color, bg }: { icon: string; label: string; value: string; color: string; bg: string }) {
  return (
    <div className="flex items-center gap-4 group cursor-default">
      <div className={`w-12 h-12 rounded-xl ${bg} flex items-center justify-center transition-transform group-hover:scale-105 shadow-sm border border-black/5`}>
        <span className={`material-symbols-outlined text-[22px] ${color}`}>{icon}</span>
      </div>
      <div className="flex flex-col justify-center">
        <span className="text-[10px] text-text-secondary uppercase font-mono tracking-widest mb-1 font-semibold">{label}</span>
        <span className="text-xl font-headline font-bold text-text-primary leading-none tracking-tight">{value}</span>
      </div>
    </div>
  )
}
