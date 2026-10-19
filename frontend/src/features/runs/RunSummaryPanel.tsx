import type { TaskRunView } from '../../api/types'

export type RunSummaryPanelProps = {
  runStatus: string
  tasks: TaskRunView[]
}

const terminalStatuses = new Set(['SUCCESS', 'FAILED', 'BLOCKED', 'CANCELLED', 'INTERRUPTED', 'NEEDS_ATTENTION'])

function RunSummaryPanel({ runStatus, tasks }: RunSummaryPanelProps) {
  const counts = new Map<string, number>()
  for (const task of tasks) counts.set(task.status, (counts.get(task.status) ?? 0) + 1)
  const orderedStatuses = [...counts.keys()].sort()
  const terminal = terminalStatuses.has(runStatus)

  return (
    <section aria-labelledby="run-summary-heading" className="run-summary-panel">
      <h2 id="run-summary-heading">Run summary</h2>
      <p data-testid="run-result">
        {terminal ? `Run result: ${runStatus}` : `Run is still in progress: ${runStatus}`}
      </p>
      <dl>
        {orderedStatuses.map((status) => (
          <div key={status}><dt>{status}</dt><dd data-testid={`status-count-${status}`}>{counts.get(status)}</dd></div>
        ))}
      </dl>
    </section>
  )
}

export default RunSummaryPanel
