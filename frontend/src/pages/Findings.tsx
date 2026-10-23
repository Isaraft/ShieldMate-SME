import { ReviewMode } from '../components/ReviewMode';
import { AssessmentSummary } from '../components/AssessmentSummary';
import { PrioritySummary } from '../components/PrioritySummary';
import { FindingFilters } from '../components/FindingFilters';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { api, ApiError } from '../authApi';
import type { Finding, FindingPage } from '../findingApi';
import { FindingState } from '../components/FindingEvidence';
import {
  Alert,
  Button,
  EmptyState,
  LoadingState,
} from '../components/ui/Primitives';
import { Table } from '../components/ui/Table';
import { scanDate } from '../scanApi';

export function Findings() {
  const [params] = useSearchParams();
  const [technical, setTechnical] = useState(false);
  return (
    <section className="findings-page">
      <p className="eyebrow">Company workspace / Evidence to action</p>
      <h1>Findings & priorities</h1>
      <p>
        Decide what to review first from the checks actually performed. These
        observations do not measure whole-company security.
      </p>
      <ReviewMode technical={technical} setTechnical={setTechnical} />
      <FindingRecords key={params.toString()} technical={technical} />
    </section>
  );
}
function FindingRecords({ technical }: { technical: boolean }) {
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState<FindingPage>();
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const navigate = useNavigate();
  const query = params.toString();
  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
      try {
        const page = await api<FindingPage>(`/findings?${query}`);
        if (!alive) return;
        setData(page);
        if (
          page.summary.assessment.pending_evaluations ||
          page.summary.assessment.in_flight_scans
        )
          timer = setTimeout(load, 3000);
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 401)
          navigate('/login', { replace: true });
        else
          setError(
            e instanceof Error ? e.message : 'Unable to load findings. Retry.',
          );
      }
    }
    void load();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [query, retry, navigate]);
  function paginate(offset: number) {
    const next = new URLSearchParams(params);
    next.set('offset', String(offset));
    setParams(next);
  }
  const coverage = data?.summary.assessment;
  return (
    <>
      {error && (
        <Alert title="Unable to load findings" tone="error">
          {error}
          <div className="button-row">
            <Button
              onClick={() => {
                setError('');
                setRetry(retry + 1);
              }}
            >
              Retry findings
            </Button>
            <Link to="/app/findings">Reset filters</Link>
          </div>
        </Alert>
      )}
      {!data && !error && <LoadingState label="Loading persisted findings…" />}
      {data && coverage && (
        <>
          <AssessmentSummary coverage={coverage} technical={technical} />
          <PrioritySummary findings={data.priorities} technical={technical} />

          <FindingFilters domains={data.domains} />

          <p role="status">
            {data.total} {data.total === 1 ? 'finding' : 'findings'} in this
            selection · {data.summary.counts_by_status.open ?? 0} open ·{' '}
            {data.summary.counts_by_status.resolved ?? 0} resolved.
          </p>
          {params.has('scan_id') && (
            <p>
              Showing findings with lineage to the selected scan. Lifecycle
              status may reflect newer evidence.
            </p>
          )}
          {data.items.length ? (
            <Table<Finding>
              caption="Persisted findings"
              rows={data.items}
              rowKey={(row) => row.id}
              columns={[
                {
                  key: 'finding',
                  title: 'Finding / affected domain',
                  render: (row) => (
                    <>
                      <Link to={`/app/findings/${row.id}`}>{row.title}</Link>
                      <p>{row.hostname}</p>
                      {technical && <code>{row.rule_id}</code>}
                    </>
                  ),
                },
                {
                  key: 'state',
                  title: 'Priority / lifecycle',
                  render: (row) => (
                    <>
                      <FindingState finding={row} />
                      <p>{row.category.replaceAll('_', ' ')}</p>
                    </>
                  ),
                },
                {
                  key: 'time',
                  title: 'Last issue observed',
                  render: (row) => (
                    <>
                      <p>{scanDate(row.last_seen_at)}</p>
                      {row.resolved_at && (
                        <p>Resolved by evidence {scanDate(row.resolved_at)}</p>
                      )}
                    </>
                  ),
                },
              ]}
            />
          ) : (
            <EmptyState
              title={
                coverage.source_scans === 0
                  ? 'No assessments yet'
                  : coverage.pending_evaluations || coverage.in_flight_scans
                    ? 'Waiting for assessment'
                    : 'No supported issues in this selection'
              }
            >
              <p>
                {coverage.source_scans === 0
                  ? 'Enroll and verify an authorized domain, then run its limited checks.'
                  : coverage.rule_counts.not_evaluable
                    ? 'Some checks could not be assessed. Unknown evidence is not a pass.'
                    : 'The evaluated conditions did not support issues matching these filters. This does not mean no security risks exist.'}
              </p>
              <Link to="/app/assets">Review authorized assets</Link>
            </EmptyState>
          )}
          <div className="button-row">
            <Button
              variant="quiet"
              disabled={data.offset === 0}
              onClick={() => paginate(Math.max(0, data.offset - data.limit))}
            >
              Previous findings
            </Button>
            <Button
              variant="quiet"
              disabled={data.offset + data.limit >= data.total}
              onClick={() => paginate(data.offset + data.limit)}
            >
              Next findings
            </Button>
          </div>
        </>
      )}
    </>
  );
}
