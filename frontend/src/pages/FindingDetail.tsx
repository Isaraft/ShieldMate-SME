import { TaskAction } from '../components/TaskAction';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, ApiError } from '../authApi';
import type { FindingDetail as Detail } from '../findingApi';
import {
  EvidenceList,
  FindingState,
  SourceLink,
} from '../components/FindingEvidence';
import { Alert, Button, LoadingState } from '../components/ui/Primitives';
import { ReviewMode } from '../components/ReviewMode';
import { scanDate } from '../scanApi';

export function FindingDetail() {
  const { findingId } = useParams();
  return <DetailRecord key={findingId} findingId={findingId!} />;
}
function DetailRecord({ findingId }: { findingId: string }) {
  const [finding, setFinding] = useState<Detail>();
  const [technical, setTechnical] = useState(false);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const navigate = useNavigate();
  useEffect(() => {
    let alive = true;
    api<Detail>(`/findings/${findingId}`)
      .then((value) => {
        if (alive) setFinding(value);
      })
      .catch((e) => {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 401)
          navigate('/login', { replace: true });
        else
          setError(
            e instanceof Error ? e.message : 'Unable to load finding. Retry.',
          );
      });
    return () => {
      alive = false;
    };
  }, [findingId, retry, navigate]);
  return (
    <section className="findings-page finding-detail">
      <p className="eyebrow">Company workspace / Evidence-backed finding</p>
      <Link to="/app/findings">Back to findings</Link>
      <h1>{finding?.title ?? 'Finding evidence'}</h1>
      {!finding && !error && <LoadingState label="Loading finding evidence…" />}
      {error && (
        <Alert title="Unable to load finding" tone="error">
          {error}
          <Button
            onClick={() => {
              setError('');
              setRetry(retry + 1);
            }}
          >
            Retry finding
          </Button>
        </Alert>
      )}
      {finding && (
        <>
          <p>{finding.hostname}</p>
          <FindingState finding={finding} />
          <TaskAction finding={finding} />
          <ReviewMode technical={technical} setTechnical={setTechnical} />
          {finding.recheck_status === 'not_rechecked' && (
            <Alert title="Verification unavailable" tone="warning">
              The latest evaluation could not recheck this rule. The last known
              lifecycle state and evidence are retained.
            </Alert>
          )}
          {finding.stale && (
            <Alert title="Historical evidence" tone="warning">
              This evidence is stale. The certificate or configuration may have
              changed since the recorded observation.
            </Alert>
          )}
          {finding.status === 'resolved' && (
            <Alert title="Resolved by comparable technical evidence">
              This specific condition was no longer observed at{' '}
              {scanDate(finding.resolved_at)}. This does not certify the whole
              site or company.
            </Alert>
          )}
          <section>
            <h2>Why this matters</h2>
            <p>{finding.impact}</p>
            <h2>Recommended next step</h2>
            <p>{finding.recommendation}</p>
            <h2>Why this priority</h2>
            <p>{finding.rationale}</p>
            <p>{finding.ranking_reason}</p>
            <h2>Limits of this conclusion</h2>
            <p>{finding.limitation}</p>
          </section>
          <dl className="finding-dates">
            <dt>First detected</dt>
            <dd>{scanDate(finding.first_seen_at)}</dd>
            <dt>Last issue observed</dt>
            <dd>{scanDate(finding.last_seen_at)}</dd>
            <dt>Current supporting evidence</dt>
            <dd>{scanDate(finding.observed_at)}</dd>
            <dt>Last evaluation</dt>
            <dd>{scanDate(finding.last_evaluation_at)}</dd>
          </dl>
          <section>
            <h2>Technical evidence & provenance</h2>
            <p>
              Rule {finding.rule_id} · Policy {finding.policy_version} ·
              Confidence: {finding.confidence}
            </p>
            <SourceLink finding={finding} />
            <details open={technical}>
              <summary>Inspect saved technical evidence</summary>
              <EvidenceList evidence={finding.evidence} />
              <p>Source scan ID: {finding.source_scan_id}</p>
              <p>Stable fingerprint: {finding.fingerprint}</p>
            </details>
          </section>
          <section>
            <h2>Finding history</h2>
            {finding.history_truncated && (
              <p>
                History was compacted: first detection, latest
                resolution/reopening and recent evaluations are retained.
              </p>
            )}
            <ol className="finding-history">
              {finding.history.map((event) => (
                <li key={event.source_scan_id}>
                  <h3>{event.kind.replaceAll('_', ' ')}</h3>
                  <p>
                    {scanDate(event.occurred_at)} ·{' '}
                    {event.snapshot.decision.replaceAll('_', ' ')} ·{' '}
                    {event.snapshot.decision === 'issue'
                      ? event.snapshot.severity + ' · '
                      : ''}
                    {event.policy_version}
                  </p>
                  <p>{event.snapshot.reason}</p>
                  {event.source_scan_available ? (
                    <Link
                      to={`/app/assets/${finding.asset_id}/scans/${event.source_scan_id}`}
                    >
                      Source scan for this event
                    </Link>
                  ) : (
                    <p>Original scan pruned; saved lineage retained.</p>
                  )}
                  {technical && (
                    <details>
                      <summary>Event evidence</summary>
                      <EvidenceList evidence={event.snapshot.evidence} />
                    </details>
                  )}
                </li>
              ))}
            </ol>
          </section>
          <p>
            Record human work in the linked task. Only a later conclusive
            authorized check can resolve this finding.
          </p>
        </>
      )}
    </section>
  );
}
