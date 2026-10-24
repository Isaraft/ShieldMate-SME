import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useLocale, tr, T, format } from '../i18n';
import { downloadPdf, type Snapshot } from '../reportApi';
import { Alert, Button, LoadingState } from '../components/ui/Primitives';
import { scanDate } from '../scanApi';
import { limitations } from '../components/ReportScope';
export function Demo() {
  const locale = useLocale();
  const [data, setData] = useState<Snapshot>(),
    [step, setStep] = useState('assets'),
    [error, setError] = useState(''),
    [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    fetch(`/api/v1/demo?locale=${locale}`, { credentials: 'omit' })
      .then(async (r) => {
        if (!r.ok) throw Error('Sample data unavailable');
        return r.json() as Promise<Snapshot>;
      })
      .then((value) => {
        if (value.kind !== 'demo') throw Error('Sample data unavailable');
        if (active) {
          setData(value);
          setError('');
        }
      })
      .catch(() => {
        if (active) setError('Sample data unavailable');
      });
    return () => {
      active = false;
    };
  }, [locale, attempt]);
  return (
    <section className="demo-page findings-page">
      <div className="demo-banner" role="note">
        <strong>
          <T text={'SAMPLE DATA / DEMO — NOT A LIVE ASSESSMENT'} />
        </strong>
        <p>
          <T
            text={
              'Fictional company, reserved example domain and a fixed scenario. No DNS proof, network checks or customer records are accessed.'
            }
          />
        </p>
      </div>
      <p className="eyebrow">
        <T text={'Read-only guided sample'} />
      </p>
      <h1>
        <T text={'From evidence to action'} />
      </h1>
      <p>
        <T
          text={
            'Explore the whole story without submitting a domain. Nothing here changes your account or starts a scan.'
          }
        />
      </p>
      <div className="button-row">
        <Link to="/register">
          <T text={'Create your own workspace'} />
        </Link>
        <Link to="/login">
          <T text={'Sign in'} />
        </Link>
        <Link to="/preview">
          <T text={'Design preview'} />
        </Link>
      </div>
      {error && (
        <Alert title={tr('Sample unavailable')} tone="error">
          {tr(error)}
          <Button onClick={() => setAttempt(attempt + 1)}>
            <T text={'Retry sample'} />
          </Button>
        </Alert>
      )}
      {!data && !error && <LoadingState label={tr('Loading sample story…')} />}
      {data && (
        <>
          <p>
            {format('demo.scenario', {
              company: data.organization_name,
              date: scanDate(data.created_at),
            })}
          </p>
          <nav className="demo-steps" aria-label={tr('Sample journey')}>
            {['assets', 'findings', 'tasks', 'report'].map((name, index) => (
              <Button
                key={name}
                variant={step === name ? 'primary' : 'quiet'}
                aria-current={step === name ? 'step' : undefined}
                onClick={() => setStep(name)}
              >
                {index + 1}.{' '}
                {tr(
                  {
                    assets: 'Sample assets',
                    findings: 'Findings and priorities',
                    tasks: 'Example work',
                    report: 'Sample PDF',
                  }[name] ?? name,
                )}
              </Button>
            ))}
          </nav>
          {step === 'assets' && (
            <section>
              <h2>
                <T text={'What was illustrated'} />
              </h2>
              <p>
                <T
                  text={
                    'These are invented observations in a fixed educational scenario, not DNS answers or a live certificate. The reserved domain cannot authorize real probes.'
                  }
                />
              </p>
              {data.assets.map((a) => (
                <article key={a.id}>
                  <h3>{a.hostname}</h3>
                  <p>
                    <T text={'Fictional domain — ownership not verified'} />
                  </p>
                  <p>
                    {format('demo.observations', {
                      count: a.observations.length,
                    })}
                  </p>
                  <details>
                    <summary>
                      <T text={'Inspect sample observations'} />
                    </summary>
                    <ul className="work-queue">
                      {a.observations.map((o) => (
                        <li key={o.id}>
                          <code>{o.check_id}</code>
                          <p>
                            {tr(o.outcome)} · {scanDate(o.observed_at)}
                          </p>
                          <code>{JSON.stringify(o.values)}</code>
                        </li>
                      ))}
                    </ul>
                  </details>
                </article>
              ))}
            </section>
          )}
          {step === 'findings' && (
            <section>
              <h2>
                <T text={'What should be reviewed first'} />
              </h2>
              <p>
                <T
                  text={
                    'The fixed scenario follows the Phase 05 policy. It demonstrates priorities without inventing a live score or CVE.'
                  }
                />
              </p>
              <ol className="priority-list">
                {data.priorities.map((f) => (
                  <li key={f.id}>
                    <h3>{tr(f.title)}</h3>
                    <p>
                      {tr(f.severity)} · {f.hostname}
                    </p>
                    <h4>
                      <T text={'Why this matters'} />
                    </h4>
                    <p>{tr(f.impact)}</p>
                    <h4>
                      <T text={'Recommended next step'} />
                    </h4>
                    <p>{tr(f.recommendation)}</p>
                    <details>
                      <summary>
                        <T text={'Sample technical evidence'} />
                      </summary>
                      <p>
                        {f.rule_id} · {scanDate(f.observed_at)}
                      </p>
                      {f.evidence.map((e) => (
                        <p key={e.observation_id}>
                          <code>
                            {e.check_id}: {JSON.stringify(e.values)}
                          </code>
                        </p>
                      ))}
                    </details>
                  </li>
                ))}
              </ol>
            </section>
          )}
          {step === 'tasks' && (
            <section>
              <h2>
                <T text={'Human work is not technical resolution'} />
              </h2>
              <p>
                <T
                  text={
                    'This read-only example includes work in different states. Marking work done does not prove a technical fix.'
                  }
                />
              </p>
              <ul className="work-queue">
                {data.tasks.map((t) => (
                  <li key={t.id}>
                    <h3>{tr(t.title)}</h3>
                    <p>
                      {tr(t.status)} · {tr('Sample IT contact')}
                    </p>
                    <p>{tr(t.recommendation)}</p>
                    {t.status === 'done' && (
                      <Alert
                        title={tr(
                          'Task marked done — remediation not yet verified',
                        )}
                        tone="warning"
                      >
                        <T
                          text={
                            'The synthetic finding is still open. A later conclusive check would be needed in a real workspace.'
                          }
                        />
                      </Alert>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}
          {step === 'report' && (
            <section>
              <h2>
                <T text={'A sample report, clearly marked'} />
              </h2>
              <p>
                <T
                  text={
                    'The backend uses the same PDF renderer and this exact synthetic dataset. Every page is marked DEMO. This is separate from protected customer report history.'
                  }
                />
              </p>
              <Button
                onClick={async () => {
                  try {
                    await downloadPdf(
                      `/demo/report?locale=${locale}`,
                      `shieldmate-DEMO-${locale}.pdf`,
                    );
                  } catch (e) {
                    setError(
                      e instanceof Error
                        ? e.message
                        : 'Unable to download PDF. Retry.',
                    );
                  }
                }}
              >
                <T text={'Download DEMO PDF'} />
              </Button>
              <p>{tr(limitations)}</p>
            </section>
          )}
        </>
      )}
      <div className="demo-endnote">
        <T text={'SAMPLE DATA / DEMO — NOT A LIVE ASSESSMENT'} />
      </div>
    </section>
  );
}
