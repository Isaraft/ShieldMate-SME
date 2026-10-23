import { Link, useSearchParams } from 'react-router-dom';
import { useWorkspaceResource } from '../hooks/useWorkspaceResource';
import type { TaskPage } from '../workflowApi';
import { TaskRows } from '../components/TaskContext';
import {
  Alert,
  Button,
  EmptyState,
  LoadingState,
} from '../components/ui/Primitives';
export function Tasks() {
  const [params] = useSearchParams();
  return <TaskRecords key={params.toString()} />;
}
function TaskRecords() {
  const [params, setParams] = useSearchParams();
  const { data, error, refresh } = useWorkspaceResource<TaskPage>(
    `/tasks?${params.toString()}`,
  );
  function paginate(offset: number) {
    const next = new URLSearchParams(params);
    next.set('offset', String(offset));
    setParams(next);
  }
  return (
    <section className="tasks-page findings-page">
      <p className="eyebrow">Company workspace / Accountable action</p>
      <h1>Action plan</h1>
      <p>
        Human work, linked to technical evidence. Completing a task never
        resolves a finding.
      </p>
      {error && (
        <Alert title="Tasks unavailable" tone="error">
          {error}
          <Button onClick={refresh}>Retry tasks</Button>
          <Link to="/app/tasks">Reset filters</Link>
        </Alert>
      )}
      {!data && !error && <LoadingState label="Loading saved tasks…" />}
      {data && (
        <>
          {error && (
            <p>Showing the last loaded snapshot; it may be out of date.</p>
          )}
          <form
            className="finding-filters"
            onSubmit={(event) => {
              event.preventDefault();
              const form = new FormData(event.currentTarget);
              const next = new URLSearchParams();
              for (const [key, value] of form)
                if (value && value !== 'all') next.set(key, String(value));
              setParams(next);
            }}
          >
            <label>
              Status
              <select
                name="status"
                defaultValue={params.get('status') ?? 'all'}
              >
                <option value="all">All work</option>
                <option value="todo">To do</option>
                <option value="in_progress">In progress</option>
                <option value="done">Done by a person</option>
              </select>
            </label>
            <label>
              Finding priority
              <select
                name="severity"
                defaultValue={params.get('severity') ?? 'all'}
              >
                <option value="all">All priorities</option>
                {['high', 'medium', 'low', 'info'].map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Domain
              <select
                name="domain_id"
                defaultValue={params.get('domain_id') ?? ''}
              >
                <option value="">All domains</option>
                {data.domains.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.hostname}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Sort
              <select
                name="sort"
                defaultValue={params.get('sort') ?? 'updated'}
              >
                <option value="updated">Last changed</option>
                <option value="oldest">First created</option>
                <option value="priority">Finding priority</option>
              </select>
            </label>
            <Button type="submit">Apply task filters</Button>
            <Link to="/app/tasks">Reset filters</Link>
          </form>
          <p role="status">
            {data.total} saved {data.total === 1 ? 'task' : 'tasks'} in this
            selection.
          </p>
          {data.items.length ? (
            <TaskRows tasks={data.items} />
          ) : (
            <EmptyState title="No tasks in this selection">
              <p>
                Start from a supported finding and create its canonical task.
                Adjust filters to review other work.
              </p>
              <Link to="/app/findings">Review findings</Link>
            </EmptyState>
          )}
          <div className="button-row">
            <Button
              disabled={data.offset === 0}
              onClick={() => paginate(Math.max(0, data.offset - data.limit))}
            >
              Previous tasks
            </Button>
            <Button
              disabled={data.offset + data.limit >= data.total}
              onClick={() => paginate(data.offset + data.limit)}
            >
              Next tasks
            </Button>
          </div>
        </>
      )}
    </section>
  );
}
