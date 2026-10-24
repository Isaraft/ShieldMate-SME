import { T, tr } from '../i18n';
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
      <p className="eyebrow">
        <T text={'Company workspace / Evidence-backed finding'} />
      </p>
      <Link to="/app/findings">
        <T text={'Back to findings'} />
      </Link>
      <h1>{tr(finding?.title ?? 'Finding evidence')}</h1>
      {!finding && !error && (
        <LoadingState label={tr('Loading finding evidence…')} />
      )}
      {error && (
        <Alert title={tr('Unable to load finding')} tone="error">
          {tr(error)}
          <Button
            onClick={() => {
              setError('');
              setRetry(retry + 1);
            }}
          >
            <T text={'Retry finding'} />
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
            <Alert title={tr('Verification unavailable')} tone="warning">
              <T
                text={
                  'The latest evaluation could not recheck this rule. The last known lifecycle state and evidence are retained.'
                }
              />
            </Alert>
          )}
          {finding.stale && (
            <Alert title={tr('Historical evidence')} tone="warning">
              <T
                text={
                  'This evidence is stale. The certificate or configuration may have changed since the recorded observation.'
                }
              />
            </Alert>
          )}
          {finding.status === 'resolved' && (
            <Alert title={tr('Resolved by comparable technical evidence')}>
              <T text={'This specific condition was no longer observed at'} />{' '}
              {scanDate(finding.resolved_at)}
              <T text={'. This does not certify the whole site or company.'} />
            </Alert>
          )}
          <section>
            <h2>
              <T text={'Why this matters'} />
            </h2>
            <p>{tr(finding.impact)}</p>
            <h2>
              <T text={'Recommended next step'} />
            </h2>
            <p>{tr(finding.recommendation)}</p>
            <h2>
              <T text={'Why this priority'} />
            </h2>
            <p>{tr(finding.rationale)}</p>
            <p>{tr(finding.ranking_reason)}</p>
            <h2>
              <T text={'Limits of this conclusion'} />
            </h2>
            <p>{tr(finding.limitation)}</p>
          </section>
          <dl className="finding-dates">
            <dt>
              <T text={'First detected'} />
            </dt>
            <dd>{scanDate(finding.first_seen_at)}</dd>
            <dt>
              <T text={'Last issue observed'} />
            </dt>
            <dd>{scanDate(finding.last_seen_at)}</dd>
            <dt>
              <T text={'Current supporting evidence'} />
            </dt>
            <dd>{scanDate(finding.observed_at)}</dd>
            <dt>
              <T text={'Last evaluation'} />
            </dt>
            <dd>{scanDate(finding.last_evaluation_at)}</dd>
          </dl>
          <section>
            <h2>
              <T text={'Technical evidence & provenance'} />
            </h2>
            <p>
              <T text={'Rule '} />
              {finding.rule_id}
              <T text={' · Policy '} />
              {finding.policy_version}
              <T text={' · Confidence: '} />
              {tr(finding.confidence)}
            </p>
            <SourceLink finding={finding} />
            <details open={technical}>
              <summary>
                <T text={'Inspect saved technical evidence'} />
              </summary>
              <EvidenceList evidence={finding.evidence} />
              <p>
                <T text={'Source scan ID: '} />
                {finding.source_scan_id}
              </p>
              <p>
                <T text={'Stable fingerprint: '} />
                {finding.fingerprint}
              </p>
            </details>
          </section>
          <section>
            <h2>
              <T text={'Finding history'} />
            </h2>
            {finding.history_truncated && (
              <p>
                <T
                  text={
                    'History was compacted: first detection, latest resolution/reopening and recent evaluations are retained.'
                  }
                />
              </p>
            )}
            <ol className="finding-history">
              {finding.history.map((event) => (
                <li key={event.source_scan_id}>
                  <h3>{tr(event.kind.replaceAll('_', ' '))}</h3>
                  <p>
                    {scanDate(event.occurred_at)} ·{' '}
                    {tr(event.snapshot.decision.replaceAll('_', ' '))} ·{' '}
                    {event.snapshot.decision === 'issue'
                      ? tr(event.snapshot.severity) + ' · '
                      : ''}
                    {event.policy_version}
                  </p>
                  <p>{tr(event.snapshot.reason)}</p>
                  {event.source_scan_available ? (
                    <Link
                      to={`/app/assets/${finding.asset_id}/scans/${event.source_scan_id}`}
                    >
                      <T text={'Source scan for this event'} />
                    </Link>
                  ) : (
                    <p>
                      <T
                        text={'Original scan pruned; saved lineage retained.'}
                      />
                    </p>
                  )}
                  {technical && (
                    <details>
                      <summary>
                        <T text={'Event evidence'} />
                      </summary>
                      <EvidenceList evidence={event.snapshot.evidence} />
                    </details>
                  )}
                </li>
              ))}
            </ol>
          </section>
          <p>
            <T
              text={
                'Record human work in the linked task. Only a later conclusive authorized check can resolve this finding.'
              }
            />
          </p>
        </>
      )}
    </section>
  );
}
