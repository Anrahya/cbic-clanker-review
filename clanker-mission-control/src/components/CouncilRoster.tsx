import { useSessionStore } from '../stores/session'

export function CouncilRoster() {
  const counsel = useSessionStore((s) => s.counsel)

  const stages = ['specialist', 'skeptic', 'arbiter'] as const
  const stageLabels = { specialist: 'STAGE_01', skeptic: 'STAGE_02', arbiter: 'STAGE_03' }

  const grouped = stages.map(stage => ({
    stage,
    label: stageLabels[stage],
    agents: counsel.filter(c => c.stage === stage),
  }))

  const getStageStatus = (agents: typeof counsel) => {
    if (agents.some(a => a.status === 'active')) return 'RUNNING'
    if (agents.every(a => a.status === 'complete')) return 'COMPLETE'
    if (agents.some(a => a.status === 'complete')) return 'RUNNING'
    return 'WAITING'
  }

  return (
    <div className="flex-1 overflow-y-auto p-5 space-y-8 bg-surface-card">
      {grouped.map(({ stage, label, agents }) => {
        const status = getStageStatus(agents)
        const isWaiting = status === 'WAITING'

        return (
          <div key={stage} className="space-y-4">
            <div className={`flex items-center justify-between ${isWaiting ? 'opacity-40' : ''}`}>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono font-bold text-text-secondary bg-surface-panel px-2 py-0.5 rounded border border-border-subtle">
                  {label}
                </span>
              </div>
              <span className={`text-[10px] font-mono font-bold tracking-widest ${
                status === 'RUNNING' ? 'text-primary-accent' :
                status === 'COMPLETE' ? 'text-emerald-600' : 'text-text-secondary'
              }`}>
                {status}
              </span>
            </div>
            <div className="space-y-2">
              {agents.map(agent => {
                const isActive = agent.status === 'active'
                const isQueued = agent.status === 'waiting'
                const isDone = agent.status === 'complete'

                return (
                  <div
                    key={agent.name}
                    className={`px-3 py-2.5 rounded-lg flex justify-between items-center transition-all ${
                      isActive
                        ? 'border border-orange-200 bg-orange-50 shadow-soft'
                        : isDone
                          ? 'border border-border-subtle bg-surface hover:bg-surface-panel'
                          : 'border border-transparent bg-transparent opacity-60'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`material-symbols-outlined text-[16px] ${
                        isActive ? 'text-primary-accent animate-spin-slow' : 
                        isDone ? 'text-emerald-600' : 'text-text-secondary'
                      }`}>
                        {isActive ? 'autorenew' : isDone ? 'task_alt' : 'schedule'}
                      </span>
                      <span className={`text-xs font-mono tracking-tight ${
                        isActive ? 'text-primary-accent font-bold' :
                        isDone ? 'text-text-primary font-medium' : 'text-text-secondary'
                      }`}>
                        {agent.displayName}
                      </span>
                    </div>
                    <span className={`text-[10px] font-mono font-semibold ${
                      isActive ? 'text-primary-accent bg-orange-100 px-1.5 py-0.5 rounded' :
                      isDone ? 'text-emerald-600' : 'text-text-secondary'
                    }`}>
                      {agent.status === 'waiting' ? (isWaiting ? '--' : 'QUEUED') :
                       agent.tokenCount > 0 ? `${(agent.tokenCount / 1000).toFixed(1)}K` :
                       isDone ? 'DONE' : '...'}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
