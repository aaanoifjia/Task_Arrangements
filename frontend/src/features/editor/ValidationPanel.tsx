import type { ValidationIssue } from './validation'
import './ValidationPanel.css'

export type ValidationPanelProps = {
  issues: ValidationIssue[]
  onSelectTask?: (taskId: string) => void
  onSave?: () => void
}

function ValidationPanel({ issues, onSelectTask, onSave }: ValidationPanelProps) {
  const hasBlockingIssues = issues.length > 0
  return (
    <section className="validation-panel" aria-label="Workflow validation">
      <div className="validation-panel__header">
        <h2>Validation</h2>
        <button type="button" onClick={() => onSave?.()} disabled={hasBlockingIssues}>Save workflow</button>
      </div>
      {hasBlockingIssues ? (
        <ul className="validation-panel__issues">
          {issues.map((issue, index) => (
            <li key={`${issue.code}-${issue.taskId ?? 'graph'}-${index}`}>
              {issue.taskId && onSelectTask
                ? <button type="button" aria-label={`Select task ${issue.taskId}`} onClick={() => onSelectTask(issue.taskId!)}>{issue.message}</button>
                : <span>{issue.message}</span>}
            </li>
          ))}
        </ul>
      ) : <p role="status">Workflow is valid.</p>}
    </section>
  )
}

export default ValidationPanel
