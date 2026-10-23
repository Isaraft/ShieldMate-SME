import { Link } from 'react-router-dom';
import type { Task } from '../workflowApi';
import { statusLabel } from '../workflowApi';
import { FindingState } from './FindingEvidence';
import { Badge, Alert } from './ui/Primitives';
import { scanDate } from '../scanApi';

export function TaskContext({ task }: { task: Task }) {
  return (
    <>
      <Badge>{statusLabel[task.status]} · human work</Badge>
      <FindingState finding={task.finding} />
      {task.status === 'done' && task.finding.status === 'open' && (
        <Alert
          title="Task marked done — remediation not yet verified"
          tone="warning"
        >
          The finding remains open. Only comparable evidence from a later
          authorized check can confirm resolution.
        </Alert>
      )}
      {task.finding.status === 'resolved' && (
        <p>
          Evidence indicates resolved at {scanDate(task.finding.resolved_at)}.
          This is separate from work completion.
        </p>
      )}
      {task.finding.stale && (
        <p>
          Historical evidence is stale. This is not a fresh security conclusion.
        </p>
      )}
      {task.finding.recheck_status === 'not_rechecked' && (
        <p>
          The latest check could not reassess this condition; its last known
          state is retained.
        </p>
      )}
      {task.reopened_at && (
        <Alert title="Recurrence recorded" tone="warning">
          The finding reopened at {scanDate(task.reopened_at)}. Review current
          evidence and explicitly move this task back to In progress if more
          work is needed. Historical notes remain unchanged.
        </Alert>
      )}
    </>
  );
}
export function TaskRows({ tasks }: { tasks: Task[] }) {
  return (
    <ul className="work-queue">
      {tasks.map((task) => (
        <li key={task.id}>
          <div>
            <Link to={`/app/tasks/${task.id}`}>{task.finding.title}</Link>
            <p>
              {task.finding.hostname} ·{' '}
              {task.owner_label || 'Owner label not set'}
            </p>
          </div>
          <p>
            {statusLabel[task.status]} · {task.finding.status} finding ·{' '}
            {task.finding.severity}
            <br />
            Updated {scanDate(task.updated_at)}
          </p>
          {task.finding.stale && <p>Stale technical evidence</p>}
          {task.finding.recheck_status === 'not_rechecked' && (
            <p>Condition not rechecked</p>
          )}
          {task.reopened_at && (
            <p>Recurrence recorded — review current evidence</p>
          )}
          {task.status === 'done' && task.finding.status === 'open' && (
            <p>Work complete; technical verification still required.</p>
          )}
        </li>
      ))}
    </ul>
  );
}
