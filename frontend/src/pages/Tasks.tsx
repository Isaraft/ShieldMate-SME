import { T, tr } from '../i18n';
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
      <p className="eyebrow">
        <T text={'Company workspace / Accountable action'} />
      </p>
      <h1>
        <T text={'Action plan'} />
      </h1>
      <p>
        <T
          text={
            'Human work, linked to technical evidence. Completing a task never resolves a finding.'
          }
        />
      </p>
      {error && (
        <Alert title={tr('Tasks unavailable')} tone="error">
          {tr(error)}
          <Button onClick={refresh}>
            <T text={'Retry tasks'} />
          </Button>
          <Link to="/app/tasks">
            <T text={'Reset filters'} />
          </Link>
        </Alert>
      )}
      {!data && !error && <LoadingState label={tr('Loading saved tasks…')} />}
      {data && (
        <>
          {error && (
            <p>
              <T
                text={
                  'Showing the last loaded snapshot; it may be out of date.'
                }
              />
            </p>
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
              <T text={'Status'} />
              <select
                name="status"
                defaultValue={params.get('status') ?? 'all'}
              >
                <option value="all">
                  <T text={'All work'} />
                </option>
                <option value="todo">
                  <T text={'To do'} />
                </option>
                <option value="in_progress">
                  <T text={'In progress'} />
                </option>
                <option value="done">
                  <T text={'Done by a person'} />
                </option>
              </select>
            </label>
            <label>
              <T text={'Finding priority'} />
              <select
                name="severity"
                defaultValue={params.get('severity') ?? 'all'}
              >
                <option value="all">
                  <T text={'All priorities'} />
                </option>
                {['high', 'medium', 'low', 'info'].map((s) => (
                  <option key={tr(s)} value={tr(s)}>
                    {tr(s)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <T text={'Domain'} />
              <select
                name="domain_id"
                defaultValue={params.get('domain_id') ?? ''}
              >
                <option value="">
                  <T text={'All domains'} />
                </option>
                {data.domains.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.hostname}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <T text={'Sort'} />
              <select
                name="sort"
                defaultValue={params.get('sort') ?? 'updated'}
              >
                <option value="updated">
                  <T text={'Last changed'} />
                </option>
                <option value="oldest">
                  <T text={'First created'} />
                </option>
                <option value="priority">
                  <T text={'Finding priority'} />
                </option>
              </select>
            </label>
            <Button type="submit">
              <T text={'Apply task filters'} />
            </Button>
            <Link to="/app/tasks">
              <T text={'Reset filters'} />
            </Link>
          </form>
          <p role="status">
            {data.total}
            <T text={' saved '} />
            <T text={data.total === 1 ? 'task' : 'tasks'} />
            <T text={' in this selection.'} />
          </p>
          {data.items.length ? (
            <TaskRows tasks={data.items} />
          ) : (
            <EmptyState title={tr('No tasks in this selection')}>
              <p>
                <T
                  text={
                    'Start from a supported finding and create its canonical task. Adjust filters to review other work.'
                  }
                />
              </p>
              <Link to="/app/findings">
                <T text={'Review findings'} />
              </Link>
            </EmptyState>
          )}
          <div className="button-row">
            <Button
              disabled={data.offset === 0}
              onClick={() => paginate(Math.max(0, data.offset - data.limit))}
            >
              <T text={'Previous tasks'} />
            </Button>
            <Button
              disabled={data.offset + data.limit >= data.total}
              onClick={() => paginate(data.offset + data.limit)}
            >
              <T text={'Next tasks'} />
            </Button>
          </div>
        </>
      )}
    </section>
  );
}
