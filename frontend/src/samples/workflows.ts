import type { WorkflowDefinition } from '../api/types'

const SAMPLE_CWD = '.'
const PLACEHOLDER_PREFIX = 'Illustrative placeholder:'

const task = (
  id: string,
  name: string,
  prompt: string,
  dependencies: string[] = [],
  execution_mode: 'NEW_THREAD' | 'CONTINUE_THREAD' = 'NEW_THREAD',
  continue_from_task_id: string | null = null,
) => ({
  id,
  name,
  prompt: `${PLACEHOLDER_PREFIX} ${prompt}`,
  cwd: SAMPLE_CWD,
  dependencies,
  execution_mode,
  continue_from_task_id,
  model: null,
  reasoning_effort: null,
  sandbox: 'workspace_write' as const,
  approval_mode: null,
  timeout_seconds: null,
  retry_policy: { max_attempts: 1 },
})

export const STARTER_WORKFLOWS: WorkflowDefinition[] = [
  {
    id: 'sample-linear',
    name: 'Linear starter',
    description: 'A small sequential workflow for learning the task graph.',
    tasks: [
      task('prepare', 'Prepare', 'Describe a preparation step; do not execute it.'),
      task('review', 'Review', 'Describe a review step; do not execute it.', ['prepare']),
    ],
    edges: [{ source_task_id: 'prepare', target_task_id: 'review' }],
  },
  {
    id: 'sample-fork-join',
    name: 'Fork/join starter',
    description: 'Two independent illustrative branches join at a final step.',
    tasks: [
      task('start', 'Start', 'Describe the shared starting point; do not execute it.'),
      task('branch-a', 'Branch A', 'Describe branch A; do not execute it.', ['start']),
      task('branch-b', 'Branch B', 'Describe branch B; do not execute it.', ['start']),
      task('finish', 'Finish', 'Describe the join step; do not execute it.', ['branch-a', 'branch-b']),
    ],
    edges: [
      { source_task_id: 'start', target_task_id: 'branch-a' },
      { source_task_id: 'start', target_task_id: 'branch-b' },
      { source_task_id: 'branch-a', target_task_id: 'finish' },
      { source_task_id: 'branch-b', target_task_id: 'finish' },
    ],
  },
  {
    id: 'sample-continuation',
    name: 'Continuation starter',
    description: 'A second step illustrates continuing an existing thread.',
    tasks: [
      task('context', 'Context', 'Describe a context step; do not execute it.'),
      task(
        'continue',
        'Continue',
        'Describe a continuation step; do not execute it.',
        ['context'],
        'CONTINUE_THREAD',
        'context',
      ),
    ],
    edges: [{ source_task_id: 'context', target_task_id: 'continue' }],
  },
]
