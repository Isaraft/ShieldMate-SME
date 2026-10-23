import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useWorkspaceResource } from '../hooks/useWorkspaceResource';
import type { DashboardData } from '../workflowApi';
import {
  Alert,
  Button,
  EmptyState,
  LoadingState,
} from '../components/ui/Primitives';
import { AssessmentSummary } from '../components/AssessmentSummary';
import { PrioritySummary } from '../components/PrioritySummary';
import { ReviewMode } from '../components/ReviewMode';
import { TaskRows } from '../components/TaskContext';
import { scanDate } from '../scanApi';

export function Dashboard() {
  const { data, error, refresh } =
    useWorkspaceResource<DashboardData>('/dashboard/summary');
  const [technical, setTechnical] = useState(false);
  return (
    <section className="dashboard findings-page">
      <p className="eyebrow">Company workspace / Decisions & action</p>
      <h1>{data?.organization.name ?? 'Your workspace'}</h1>
      <p className="dashboard-intro">
        Know what deserves attention. Record the work. Verify it with evidence.
      </p>
      {error && (
        <Alert title="Overview unavailable" tone="error">
          {error}
          <Button onClick={refresh}>Retry overview</Button>
        </Alert>
      )}
      {!data && !error && <LoadingState label="Loading your workspace…" />}
      {data && (
        <>
          <p className="field-help">
            Last useful observation: {scanDate(data.last_useful_observation_at)}{' '}
            · Overview read {scanDate(data.generated_at)}.
          </p>
          {error && (
            <p>
              The records below are the last loaded snapshot and may be out of
              date.
            </p>
          )}
          <ReviewMode technical={technical} setTechnical={setTechnical} />
          <dl className="operating-strip">
            <div>
              <dt>Fresh ownership proofs</dt>
              <dd>
                <Link to="/app/assets">
                  {data.verified_assets} / {data.asset_count} domains
                </Link>
              </dd>
            </div>
            <div>
              <dt>Supported open findings</dt>
              <dd>
                <Link to="/app/findings?status=open">
                  {data.findings.total}
                </Link>
              </dd>
            </div>
            <div>
              <dt>Human work in progress</dt>
              <dd>
                <Link to="/app/tasks?status=in_progress">
                  {data.task_counts.in_progress ?? 0}
                </Link>
              </dd>
            </div>
            <div>
              <dt>Work marked done</dt>
              <dd>
                <Link to="/app/tasks?status=done">
                  {data.task_counts.done ?? 0}
                </Link>
              </dd>
            </div>
          </dl>
          {data.asset_count === 0 ? (
            <EmptyState title="Start with a domain you control">
              <p>
                Your workspace is saved. Add a domain and publish its TXT
                ownership proof before any checks.
              </p>
              <Link to="/app/assets">Add an authorized domain</Link>
            </EmptyState>
          ) : data.eligible_assets === 0 ? (
            <Alert title="Ownership needs attention" tone="warning">
              No enrolled domain currently meets authorization and proof
              requirements.{' '}
              <Link to="/app/assets">Review domain ownership</Link>.
            </Alert>
          ) : data.recent_scan_count === 0 ? (
            <Alert title="Ready for the first assessment">
              {data.eligible_assets} domains meet ownership requirements. No
              scans are recorded.{' '}
              <Link to="/app/assets">Open authorized scan controls</Link>;
              quotas and safety checks still apply.
            </Alert>
          ) : null}
          {data.done_unverified > 0 && (
            <Alert
              title="Human work is not technical resolution"
              tone="warning"
            >
              {data.done_unverified} tasks are marked done while their findings
              remain open.{' '}
              <Link to="/app/tasks?status=done">
                Review work awaiting verification
              </Link>
              .
            </Alert>
          )}
          <PrioritySummary
            findings={data.findings.priorities}
            technical={technical}
          />
          <Link to="/app/findings">Review all findings and evidence</Link>
          <AssessmentSummary
            coverage={data.findings.summary.assessment}
            technical={technical}
          />
          {data.scans.some((s) =>
            ['partial', 'failed', 'interrupted'].includes(s.status),
          ) && (
            <Alert title="Some recent checks were incomplete" tone="warning">
              Collection errors do not prove safety or remediation. Review the
              recorded scope and unavailable observations.
            </Alert>
          )}
          <div className="dashboard-columns">
            <section>
              <div className="section-heading">
                <h2>Remediation queue</h2>
                <Link to="/app/tasks">All tasks</Link>
              </div>
              <p>
                To do: {data.task_counts.todo ?? 0} · In progress:{' '}
                {data.task_counts.in_progress ?? 0} · Done by a person:{' '}
                {data.task_counts.done ?? 0}. Up to five recently changed tasks.
              </p>
              {data.tasks.length ? (
                <TaskRows tasks={data.tasks} />
              ) : (
                <p>
                  No tasks yet. Create a task from a supported open finding; no
                  work is generated automatically.
                </p>
              )}
            </section>
            <section>
              <div className="section-heading">
                <h2>Recent scans</h2>
                <Link to="/app/assets">Assets & scan history</Link>
              </div>
              <p>
                {data.recent_scan_count} retained runs for current assets.
                Showing up to five latest.
              </p>
              {data.scans.length ? (
                <ul className="work-queue">
                  {data.scans.map((s) => (
                    <li key={s.id}>
                      <Link to={`/app/assets/${s.asset_id}/scans/${s.id}`}>
                        {s.hostname}
                      </Link>
                      <p>
                        {s.status} · {s.completed_checks} collected observations
                        <br />
                        {scanDate(s.finished_at ?? s.created_at)}
                      </p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No scan history. No safety conclusion is available.</p>
              )}
            </section>
          </div>
          <section>
            <h2>Recent work activity</h2>
            <p>Up to five saved task events. Changes describe human work.</p>
            {data.activity.length ? (
              <ol className="work-queue">
                {data.activity.map((e) => (
                  <li key={`${e.task_id}:${e.version}`}>
                    <Link to={`/app/tasks/${e.task_id}`}>{e.title}</Link>
                    <p>
                      {e.actor_label} · {e.kind} · revision {e.version} ·{' '}
                      {scanDate(e.created_at)}
                    </p>
                  </li>
                ))}
              </ol>
            ) : (
              <p>No task changes have been recorded.</p>
            )}
          </section>
        </>
      )}
    </section>
  );
}
