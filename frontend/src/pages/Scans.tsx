import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, ApiError } from '../authApi';
import {
  Alert,
  Badge,
  Button,
  EmptyState,
  LoadingState,
} from '../components/ui/Primitives';
import {
  type History,
  type ScanDetail,
  isActive,
  scanDate,
  scanErrors,
} from '../scanApi';

const labels = {
  pass: 'No issue observed for this check',
  attention: 'Needs attention',
  informational: 'Configuration context',
  inconclusive: 'Failed to check',
  error: 'Failed to check',
};
export function Scans() {
  const { domainId, scanId } = useParams();
  return <ScanRecords key={`${domainId}/${scanId}`} />;
}
function ScanRecords() {
  const { domainId, scanId } = useParams();
  const navigate = useNavigate();
  const [history, setHistory] = useState<History>();
  const [scan, setScan] = useState<ScanDetail>();
  const [error, setError] = useState('');
  const [offset, setOffset] = useState(0);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;
    const path = `/domains/${domainId}/scans`;
    async function load() {
      try {
        if (scanId) {
          const detail = await api<ScanDetail>(`${path}/${scanId}`);
          if (!alive) return;
          setScan(detail);
          if (isActive(detail.status)) timer = setTimeout(load, 2000);
        } else {
          const rows = await api<History>(`${path}?offset=${offset}&limit=10`);
          if (!alive) return;
          setHistory(rows);
          if (rows.items.some((row) => isActive(row.status)))
            timer = setTimeout(load, 3000);
        }
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 401)
          navigate('/login', { replace: true });
        else
          setError(
            e instanceof Error ? e.message : 'Unable to load scans. Retry.',
          );
      }
    }
    void load();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [domainId, scanId, offset, retry, navigate]);
  const base = `/app/assets/${domainId}/scans`;
  return (
    <section className="scans-page">
      <p className="eyebrow">Company workspace / Technical observations</p>
      <h1>{scanId ? 'Security check record' : 'Scan history'}</h1>
      <p>
        ShieldMate Starter performs limited external configuration checks. It
        does not guarantee security or detect all vulnerabilities.
      </p>
      <div className="button-row">
        {scanId && (
          <Link
            className="button button-secondary"
            to={`/app/findings?domain_id=${domainId}&scan_id=${scanId}`}
          >
            Review derived findings
          </Link>
        )}
        <Link className="button button-secondary" to="/app/assets">
          Back to assets
        </Link>
        {scanId && (
          <Link className="button button-quiet" to={base}>
            View scan history
          </Link>
        )}
      </div>
      {error && (
        <>
          <Alert tone="error" title="Unable to load scan records">
            {error}
          </Alert>
          <Button
            onClick={() => {
              setError('');
              setRetry(retry + 1);
            }}
          >
            Retry loading scans
          </Button>
        </>
      )}
      {!error && !scan && !history && (
        <LoadingState label="Loading scan records…" />
      )}
      {history && (
        <>
          {!history.items.length ? (
            <EmptyState title="No completed scans yet">
              <p>
                Enroll and verify an authorized domain in Assets, then run its
                limited security checks.
              </p>
            </EmptyState>
          ) : (
            <ol className="scan-history">
              {history.items.map((row) => (
                <li key={row.id}>
                  <div>
                    <h2>{row.hostname}</h2>
                    <p>{scanDate(row.created_at)}</p>
                    <Badge>{row.status}</Badge>
                    <p>
                      {row.completed_checks} of {row.total_checks} check
                      outcomes recorded
                    </p>
                  </div>
                  <Link
                    className="button button-secondary"
                    to={`${base}/${row.id}`}
                  >
                    View scan record
                  </Link>
                </li>
              ))}
            </ol>
          )}
          <div className="button-row">
            <Button
              variant="quiet"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - 10))}
            >
              Newer scans
            </Button>
            <Button
              variant="quiet"
              disabled={offset + 10 >= history.total}
              onClick={() => setOffset(offset + 10)}
            >
              Older scans
            </Button>
          </div>
        </>
      )}
      {scan && (
        <>
          <div className="scan-summary" role="status">
            <h2>{scan.hostname}</h2>
            <Badge tone={scan.status === 'completed' ? 'success' : 'neutral'}>
              {scan.status}
            </Badge>
            <p>
              {scan.completed_checks} of {scan.total_checks} check outcomes
              recorded.{' '}
              {isActive(scan.status)
                ? 'Updates arrive automatically. Unrecorded checks have not been checked yet.'
                : 'This record is stored; it does not update automatically.'}
            </p>
            <dl>
              <dt>Requested</dt>
              <dd>{scanDate(scan.created_at)}</dd>
              <dt>Started</dt>
              <dd>{scanDate(scan.started_at)}</dd>
              <dt>Finished</dt>
              <dd>{scanDate(scan.finished_at)}</dd>
              <dt>Engine</dt>
              <dd>{scan.engine_version}</dd>
            </dl>
          </div>
          {scan.error_code && (
            <Alert title="Scan limitation" tone="warning">
              {scanErrors[scan.error_code] ??
                `The scan could not fully complete (${scan.error_code}). No blanket security conclusion is available.`}
            </Alert>
          )}
          {(['DNS', 'TLS', 'HTTP'] as const).map((group) => {
            const observations = scan.observations.filter((row) =>
              row.check_id.startsWith(group),
            );
            return (
              <section
                className="observation-group"
                key={group}
                aria-label={`${group} observations`}
              >
                <h2>{group === 'HTTP' ? 'HTTP & HTTPS' : group}</h2>
                {!observations.length && (
                  <p>Not checked — no observations recorded yet.</p>
                )}
                {observations.map((row) => (
                  <article className="observation" key={row.check_id}>
                    <p className="eyebrow">{row.check_id}</p>
                    <h3>{row.summary}</h3>
                    <Badge
                      tone={
                        row.outcome === 'pass'
                          ? 'success'
                          : row.outcome === 'attention'
                            ? 'warning'
                            : 'neutral'
                      }
                    >
                      {labels[row.outcome]}
                    </Badge>
                    <p>{row.explanation}</p>
                    <details>
                      <summary>Technical evidence</summary>
                      <p>
                        Source: {row.source} · Observed{' '}
                        {scanDate(row.observed_at)} · Asset: {scan.hostname}
                      </p>
                      <dl>
                        {Object.entries(row.evidence).map(([key, value]) => (
                          <div key={key}>
                            <dt>{key.replaceAll('_', ' ')}</dt>
                            <dd>
                              <code>
                                {Array.isArray(value)
                                  ? value.join(', ')
                                  : String(value)}
                              </code>
                            </dd>
                          </div>
                        ))}
                      </dl>
                    </details>
                  </article>
                ))}
              </section>
            );
          })}
        </>
      )}
    </section>
  );
}
