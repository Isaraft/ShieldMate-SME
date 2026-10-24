import { PrioritySummary } from '../components/PrioritySummary';
import { useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, ApiError } from '../authApi';
import { useWorkspaceResource } from '../hooks/useWorkspaceResource';
import { useLocale, tr, T, localeName, type Locale } from '../i18n';
import {
  downloadPdf,
  type ReportHistory,
  type ReportMeta,
  type Snapshot,
} from '../reportApi';
import { ReportScope } from '../components/ReportScope';
import { Alert, Button, LoadingState } from '../components/ui/Primitives';
import { scanDate } from '../scanApi';
export function Reports() {
  const locale = useLocale();
  const navigate = useNavigate();
  const [offset, setOffset] = useState(0);
  const overview = useWorkspaceResource<Snapshot>('/reports/overview');
  const history = useWorkspaceResource<ReportHistory>(
    `/reports?offset=${offset}&limit=10`,
  );
  const [pending, setPending] = useState(false),
    [error, setError] = useState(''),
    [message, setMessage] = useState('');
  const requestKey = useRef<{ key: string; locale: Locale } | undefined>(
    undefined,
  );
  async function download(record: ReportMeta) {
    setError('');
    try {
      await downloadPdf(
        `/reports/${record.id}/download`,
        `shieldmate-${record.id}-${record.locale}.pdf`,
      );
      setMessage('PDF download started. This saved artifact will not change.');
    } catch (e) {
      if (e instanceof ApiError && e.status === 401)
        navigate('/login', { replace: true });
      else
        setError(
          e instanceof Error ? e.message : 'Unable to download PDF. Retry.',
        );
    }
  }
  return (
    <section className="reports-page findings-page">
      <p className="eyebrow">
        <T text={'Company workspace / Evidence to share'} />
      </p>
      <h1>
        <T text={'Security snapshots'} />
      </h1>
      <p>
        <T
          text={
            'Save an immutable account of the evidence available now. This is not a monthly trend or a security certificate.'
          }
        />
      </p>
      {(error || overview.error || history.error) && (
        <Alert title={tr('Reports unavailable')} tone="error">
          {tr(error || overview.error || history.error)}
          <Button
            onClick={() => {
              setError('');
              overview.refresh();
              history.refresh();
            }}
          >
            <T text={'Retry reports'} />
          </Button>
        </Alert>
      )}
      {!overview.data && !overview.error && (
        <LoadingState label={tr('Loading report readiness…')} />
      )}
      {overview.data && (
        <>
          <ReportScope snapshot={overview.data} />
          <section>
            <h2>
              <T text="Finding and work summary" />
            </h2>
            <dl className="coverage-counts">
              {Object.entries(overview.data.finding_counts).map(
                ([key, count]) => (
                  <div key={key}>
                    <dt>
                      {key
                        .split(':')
                        .map((trValue) => tr(trValue))
                        .join(' · ')}
                    </dt>
                    <dd>{count}</dd>
                  </div>
                ),
              )}
            </dl>
            <p>
              <T text="Human task status does not determine finding resolution." />
            </p>
            <dl className="coverage-counts">
              {Object.entries(overview.data.task_counts).map(([key, count]) => (
                <div key={key}>
                  <dt>{tr(key)}</dt>
                  <dd>{count}</dd>
                </div>
              ))}
            </dl>
            <PrioritySummary
              findings={overview.data.priorities}
              technical={false}
            />
          </section>
          <div className="button-row">
            <Button
              pending={pending}
              disabled={!overview.data.can_generate}
              onClick={async () => {
                setPending(true);
                setError('');
                setMessage('');
                if (requestKey.current?.locale !== locale)
                  requestKey.current = { key: crypto.randomUUID(), locale };
                try {
                  const record = await api<ReportMeta>('/reports', 'POST', {
                    locale,
                    request_key: requestKey.current!.key,
                  });
                  requestKey.current = undefined;
                  history.refresh();
                  if (record.status === 'failed')
                    setError(
                      'PDF generation failed. No broken document was published. Retry with a new attempt.',
                    );
                  else if (record.status === 'generating')
                    setMessage(
                      'PDF generation is still running. History updates automatically.',
                    );
                  else
                    setMessage('PDF snapshot saved. Download it from history.');
                } catch (e) {
                  if (e instanceof ApiError && e.status === 401) {
                    navigate('/login', { replace: true });
                  } else
                    setError(
                      e instanceof Error
                        ? e.message
                        : 'Unable to generate PDF. Retry.',
                    );
                } finally {
                  setPending(false);
                }
              }}
            >
              <T text={'Generate PDF Snapshot'} />
            </Button>
            <Link to="/app/assets">
              <T text={'Review ownership and scans'} />
            </Link>
          </div>
          <p>
            <T
              text={
                'Up to five attempts per hour and 20 saved snapshots per workspace. No silent overwrite. A snapshot includes at most 20 domains, 120 findings, 120 tasks, 80 pages and 2 MiB.'
              }
            />
          </p>
          {!overview.data.can_generate && (
            <Alert title={tr('No qualifying report data')}>
              <T
                text={
                  'Verify an authorized domain, collect its limited observations and allow the worker to evaluate them. Failed or missing checks are not a clean assessment.'
                }
              />
            </Alert>
          )}
        </>
      )}
      {message && <p role="status">{tr(message)}</p>}
      <section>
        <h2>
          <T text={'Saved report history'} />
        </h2>
        <p>
          <T
            text={
              'Stored PDFs retain their original evidence, language and checksum after later changes. Generation time and observation time are separate.'
            }
          />
        </p>
        {!history.data && !history.error && (
          <LoadingState label={tr('Loading saved reports…')} />
        )}
        {history.data && (
          <>
            <p role="status">
              {history.data.total}
              <T text={' saved snapshots.'} />
            </p>
            {history.data.items.length ? (
              <ul className="work-queue">
                {history.data.items.map((r) => (
                  <li key={r.id}>
                    <h3>
                      {scanDate(r.created_at)} · {r.locale.toUpperCase()}
                    </h3>
                    <p>
                      {tr(r.status)} ·{' '}
                      {r.byte_count.toLocaleString(localeName())}
                      <T text={' bytes'} />
                    </p>
                    <p className="field-help">{r.id}</p>
                    {r.sha256 && (
                      <p className="report-checksum">
                        <T text={'SHA-256: '} />
                        {r.sha256}
                      </p>
                    )}
                    {r.status === 'ready' && (
                      <Button onClick={() => void download(r)}>
                        <T text={'Download PDF'} />
                      </Button>
                    )}
                    {r.status === 'failed' && (
                      <p>
                        <T
                          text={
                            'Generation failed. No PDF is available for this attempt.'
                          }
                        />
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p>
                <T text={'No saved snapshots yet.'} />
              </p>
            )}
            <div className="button-row">
              <Button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - 10))}
              >
                <T text={'Previous reports'} />
              </Button>
              <Button
                disabled={offset + 10 >= history.data.total}
                onClick={() => setOffset(offset + 10)}
              >
                <T text={'Next reports'} />
              </Button>
            </div>
          </>
        )}
      </section>
    </section>
  );
}
