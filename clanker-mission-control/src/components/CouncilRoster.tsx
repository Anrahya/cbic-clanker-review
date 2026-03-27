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
    <>
      {grouped.map(({ stage, label, agents }) => {
        const status = getStageStatus(agents)
        const isWaiting = status === 'WAITING'

        return (
          <div key={stage} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="roster-stage-header" style={{ opacity: isWaiting ? 0.4 : 1 }}>
              <span className="stage-badge">{label}</span>
              <span className={`stage-status ${status.toLowerCase()}`}>
                {status}
              </span>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {agents.map(agent => {
                const isActive = agent.status === 'active'
                const isDone = agent.status === 'complete'
                const statusClass = isActive ? 'active' : isDone ? 'complete' : 'waiting'

                return (
                  <div key={agent.name} className={`agent-row ${statusClass}`}>
                    <div className="agent-name">
                      <span className={`material-symbols-outlined ${isActive ? 'animate-spin-slow' : ''}`}>
                        {isActive ? 'autorenew' : isDone ? 'task_alt' : 'schedule'}
                      </span>
                      {agent.displayName}
                    </div>
                    <span className="agent-metric">
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
    </>
  )
}
