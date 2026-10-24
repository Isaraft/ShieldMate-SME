import { T, tr } from '../i18n';
import { Link } from 'react-router-dom';
import type { Task } from '../workflowApi';
import { statusLabel } from '../workflowApi';
import { FindingState } from './FindingEvidence';
import { Badge, Alert } from './ui/Primitives';
import { scanDate } from '../scanApi';

export function TaskContext({ task }: { task: Task }) {
  return (
    <>
      <Badge>
        {tr(statusLabel[task.status])}
        <T text={' · human work'} />
      </Badge>
      <FindingState finding={task.finding} />
      {task.status === 'done' && task.finding.status === 'open' && (
        <Alert
          title={tr('Task marked done — remediation not yet verified')}
          tone="warning"
        >
          <T
            text={
              'The finding remains open. Only comparable evidence from a later authorized check can confirm resolution.'
            }
          />
        </Alert>
      )}
      {task.finding.status === 'resolved' && (
        <p>
          <T text={'Evidence indicates resolved at '} />
          {scanDate(task.finding.resolved_at)}
          <T text={'. This is separate from work completion.'} />
        </p>
      )}
      {task.finding.stale && (
        <p>
          <T
            text={
              'Historical evidence is stale. This is not a fresh security conclusion.'
            }
          />
        </p>
      )}
      {task.finding.recheck_status === 'not_rechecked' && (
        <p>
          <T
            text={
              'The latest check could not reassess this condition; its last known state is retained.'
            }
          />
        </p>
      )}
      {task.reopened_at && (
        <Alert title={tr('Recurrence recorded')} tone="warning">
          <T text={'The finding reopened at '} />
          {scanDate(task.reopened_at)}
          <T
            text={
              '. Review current evidence and explicitly move this task back to In progress if more work is needed. Historical notes remain unchanged.'
            }
          />
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
            <Link to={`/app/tasks/${task.id}`}>{tr(task.finding.title)}</Link>
            <p>
              {task.finding.hostname} ·{' '}
              {task.owner_label || tr('Owner label not set')}
            </p>
          </div>
          <p>
            {tr(statusLabel[task.status])} · {tr(task.finding.status)}
            <T text={' finding ·'} /> {tr(task.finding.severity)}
            <br />
            <T text={'Updated '} />
            {scanDate(task.updated_at)}
          </p>
          {task.finding.stale && (
            <p>
              <T text={'Stale technical evidence'} />
            </p>
          )}
          {task.finding.recheck_status === 'not_rechecked' && (
            <p>
              <T text={'Condition not rechecked'} />
            </p>
          )}
          {task.reopened_at && (
            <p>
              <T text={'Recurrence recorded — review current evidence'} />
            </p>
          )}
          {task.status === 'done' && task.finding.status === 'open' && (
            <p>
              <T
                text={'Work complete; technical verification still required.'}
              />
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}
