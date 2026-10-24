import { T, tr } from '../i18n';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, ApiError } from '../authApi';
import { useWorkspaceResource } from '../hooks/useWorkspaceResource';
import type { TaskDetail as Detail, TaskStatus } from '../workflowApi';
import { statusLabel } from '../workflowApi';
import { TaskContext } from '../components/TaskContext';
import { SourceLink } from '../components/FindingEvidence';
import {
  Alert,
  Button,
  Field,
  LoadingState,
} from '../components/ui/Primitives';
import { scanDate } from '../scanApi';

export function TaskDetail() {
  const { taskId } = useParams();
  return <TaskRecord key={taskId} id={taskId!} />;
}
function TaskRecord({ id }: { id: string }) {
  const { data, error, refresh } = useWorkspaceResource<Detail>(
    `/tasks/${id}`,
    0,
  );
  return (
    <section className="task-detail findings-page">
      <p className="eyebrow">
        <T text={'Company workspace / Remediation task'} />
      </p>
      <Link to="/app/tasks">
        <T text={'Back to action plan'} />
      </Link>
      <h1>{tr(data?.finding.title ?? 'Task record')}</h1>
      {error && (
        <Alert title={tr('Task unavailable')} tone="error">
          {tr(error)}
          <Button onClick={refresh}>
            <T text={'Retry task'} />
          </Button>
        </Alert>
      )}
      {!data && !error && <LoadingState label={tr('Loading saved task…')} />}
      {data && (
        <>
          <p>{data.finding.hostname}</p>
          <TaskContext task={data} />
          <section>
            <h2>
              <T text={'Evidence & next action'} />
            </h2>
            <p>{tr(data.finding.impact)}</p>
            <p>{tr(data.finding.recommendation)}</p>
            <div className="button-row">
              <Link to={`/app/findings/${data.finding_id}`}>
                <T text={'Review finding & technical history'} />
              </Link>
              <SourceLink finding={data.finding} />
              <Link to={`/app/assets#asset-${data.finding.asset_id}`}>
                <T text={'Recheck ownership & scan controls'} />
              </Link>
            </div>
            <p>
              <T
                text={
                  'New checks require current authorization and fresh ownership proof. Existing quotas and network controls apply.'
                }
              />
            </p>
          </section>
          <TaskEditor key={data.id} task={data} onSaved={refresh} />
          <p>
            <T text={'Created '} />
            {scanDate(data.created_at)}
            <T text={' · Updated'} /> {scanDate(data.updated_at)}
            <T text={' · Work completed'} /> {scanDate(data.completed_at)}.
          </p>
          <section>
            <h2>
              <T text={'Work history'} />
            </h2>
            {data.history_truncated && (
              <p>
                <T
                  text={
                    'History compacted: first creation and the latest 99 changes are retained.'
                  }
                />
              </p>
            )}
            <ol className="finding-history">
              {data.history.map((e) => (
                <li key={e.id}>
                  <h3>
                    {tr(e.kind)}
                    <T text={' · revision '} />
                    {e.version}
                  </h3>
                  <p>
                    {tr(e.actor_label)} · {scanDate(e.created_at)}
                  </p>
                  <dl>
                    {Object.entries(e.changes).map(([field, change]) => (
                      <div key={field}>
                        <dt>{tr(field.replaceAll('_', ' '))}</dt>
                        <dd>
                          <span className="note-text">
                            {change.old
                              ? field === 'status'
                                ? tr(change.old)
                                : change.old
                              : tr('(empty)')}
                          </span>{' '}
                          →{' '}
                          <span className="note-text">
                            {change.new
                              ? field === 'status'
                                ? tr(change.new)
                                : change.new
                              : tr('(empty)')}
                          </span>
                        </dd>
                      </div>
                    ))}
                  </dl>
                </li>
              ))}
            </ol>
          </section>
          <p>
            <T
              text={
                'Tasks cannot be deleted or archived in this MVP; move work back to To do or In progress to correct it. Removing its domain deletes the linked task and work history.'
              }
            />
          </p>
        </>
      )}
    </section>
  );
}
function TaskEditor({ task, onSaved }: { task: Detail; onSaved: () => void }) {
  const [status, setStatus] = useState<TaskStatus>(task.status),
    [owner, setOwner] = useState(task.owner_label),
    [note, setNote] = useState(task.note);
  const [pending, setPending] = useState(false),
    [error, setError] = useState(''),
    [conflict, setConflict] = useState(false),
    [message, setMessage] = useState('');
  const navigate = useNavigate();
  const [base, setBase] = useState(task);
  const dirty =
    status !== base.status || owner !== base.owner_label || note !== base.note;
  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = '';
    };
    const navigation = (e: MouseEvent) => {
      if (
        e.defaultPrevented ||
        e.button !== 0 ||
        e.ctrlKey ||
        e.metaKey ||
        e.shiftKey ||
        e.altKey
      )
        return;
      const link = e.target instanceof Element ? e.target.closest('a') : null;
      if (!link || link.target === '_blank' || link.hasAttribute('download'))
        return;
      if (
        link.href !== window.location.href &&
        !window.confirm(tr('Discard unsaved work changes and leave this task?'))
      ) {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    if (dirty) {
      window.addEventListener('beforeunload', warn);
      document.addEventListener('click', navigation, true);
    }
    return () => {
      window.removeEventListener('beforeunload', warn);
      document.removeEventListener('click', navigation, true);
    };
  }, [dirty]);
  return (
    <section>
      <h2>
        <T text={'Record the work'} />
      </h2>
      <form
        className="task-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setPending(true);
          setError('');
          setMessage('');
          try {
            const saved = await api<Detail>(`/tasks/${task.id}`, 'PATCH', {
              version: base.version,
              status,
              owner_label: owner,
              note,
            });
            setBase(saved);
            setStatus(saved.status);
            setOwner(saved.owner_label);
            setNote(saved.note);
            setMessage(
              'Work changes saved. Technical finding state is unchanged.',
            );
            onSaved();
          } catch (e) {
            if (e instanceof ApiError && e.status === 401)
              navigate('/login', { replace: true });
            else {
              setConflict(e instanceof ApiError && e.status === 409);
              setError(
                e instanceof Error ? e.message : 'Unable to save. Retry.',
              );
            }
          } finally {
            setPending(false);
          }
        }}
      >
        <label htmlFor="task-status">
          <T text={'Work status'} />
        </label>
        <select
          id="task-status"
          value={status}
          onChange={(e) => setStatus(e.target.value as TaskStatus)}
        >
          {Object.entries(statusLabel).map(([value, label]) => (
            <option key={value} value={value}>
              {tr(label)}
            </option>
          ))}
        </select>
        <Field
          label={tr('Owner label')}
          help={tr(
            'Descriptive responsibility, not a user account or permission. Up to 80 characters.',
          )}
          maxLength={80}
          value={owner}
          onChange={(e) => setOwner(e.target.value)}
        />
        <label htmlFor="task-note">
          <T text={'Work note'} />
        </label>
        <textarea
          id="task-note"
          maxLength={2000}
          rows={6}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          aria-describedby="note-help"
        />
        <p id="note-help" className="field-help">
          {note.length}
          <T
            text={
              '/2000 characters. Do not store passwords, tokens or customer personal data.'
            }
          />
        </p>
        {dirty && (
          <p role="status">
            <T text={'Unsaved work changes.'} />
          </p>
        )}
        {error && (
          <Alert title={tr('Unable to save task')} tone="error">
            {tr(error)}
          </Alert>
        )}
        {message && <p role="status">{tr(message)}</p>}
        <div className="button-row">
          <Button type="submit" pending={pending} disabled={!dirty || conflict}>
            <T text={'Save work changes'} />
          </Button>
          <Button
            variant="quiet"
            disabled={!dirty || pending}
            onClick={() => {
              setStatus(base.status);
              setOwner(base.owner_label);
              setNote(base.note);
              setError('');
              setConflict(false);
            }}
          >
            <T text={'Discard draft'} />
          </Button>
          {conflict && (
            <Button
              onClick={async () => {
                try {
                  const latest = await api<Detail>(`/tasks/${task.id}`);
                  setBase(latest);
                  setStatus(latest.status);
                  setOwner(latest.owner_label);
                  setNote(latest.note);
                  setConflict(false);
                  setError('');
                  onSaved();
                } catch (e) {
                  setError(
                    e instanceof Error
                      ? e.message
                      : 'Unable to reload task. Retry.',
                  );
                }
              }}
            >
              <T text={'Reload latest and discard draft'} />
            </Button>
          )}
        </div>
      </form>
    </section>
  );
}
