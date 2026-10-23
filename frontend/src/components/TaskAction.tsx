import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, ApiError } from '../authApi';
import type { Finding } from '../findingApi';
import type { Task } from '../workflowApi';
import { Button } from './ui/Primitives';

export function TaskAction({ finding }: { finding: Finding }) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  if (finding.task_id)
    return (
      <Link to={`/app/tasks/${finding.task_id}`}>
        Open task · {finding.task_status?.replaceAll('_', ' ')}
      </Link>
    );
  if (finding.status !== 'open')
    return <p>No new task needed for this resolved condition.</p>;
  return (
    <div className="task-action">
      <Button
        pending={pending}
        onClick={async () => {
          setPending(true);
          setError('');
          try {
            const task = await api<Task>(
              `/findings/${finding.id}/task`,
              'POST',
              {},
            );
            navigate(`/app/tasks/${task.id}`);
          } catch (e) {
            if (e instanceof ApiError && e.status === 401)
              navigate('/login', { replace: true });
            else
              setError(
                e instanceof Error
                  ? e.message
                  : 'Unable to create task. Retry.',
              );
          } finally {
            setPending(false);
          }
        }}
      >
        Create task
      </Button>
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
