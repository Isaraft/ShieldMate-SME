import type { Snapshot } from '../reportApi';
import { tr, T, format } from '../i18n';
import { scanDate } from '../scanApi';
export const limitations =
  'This is a limited external configuration assessment, not a penetration test, compliance audit or guarantee of safety. Missing, failed or stale checks do not prove security. Human task completion is not technical resolution.';
export function ReportScope({ snapshot }: { snapshot: Snapshot }) {
  return (
    <section className="report-scope">
      <h2>
        <T text={'Evidence and assessed scope'} />
      </h2>
      <p>{tr(snapshot.readiness)}</p>
      <dl className="operating-strip">
        <div>
          <dt>
            <T text={'Enrolled domains'} />
          </dt>
          <dd>{snapshot.counts.enrolled_domains}</dd>
        </div>
        <div>
          <dt>
            <T text={'Currently authorized domains'} />
          </dt>
          <dd>{snapshot.counts.authorized_domains}</dd>
        </div>
        <div>
          <dt>
            <T text={'Domains with usable saved evidence'} />
          </dt>
          <dd>{snapshot.counts.assessed_domains}</dd>
        </div>
        <div>
          <dt>
            <T text={'Domains without usable evidence'} />
          </dt>
          <dd>{snapshot.counts.without_usable_evidence}</dd>
        </div>
      </dl>
      <p>
        <T
          text={
            'Current ownership is not inferred from an old scan. Only saved observations matching current authorization and policy can enter assessed scope.'
          }
        />
      </p>
      <p>
        {format('report.excluded', {
          count: snapshot.counts.excluded_historical_findings,
        })}
      </p>
      <ul className="work-queue">
        {snapshot.assets.map((a) => (
          <li key={a.id}>
            <h3>{a.hostname}</h3>
            <p>
              {tr(a.reason)} · {tr(a.scan_status ?? 'not_checked')} ·{' '}
              {scanDate(a.scan_finished_at)}
            </p>
            {a.stale && (
              <p>
                <T text={'Historical evidence — stale'} />
              </p>
            )}
            <p>
              {Object.entries(a.observation_counts)
                .map(([key, count]) => `${tr(key)}: ${count}`)
                .join(' · ')}
            </p>
          </li>
        ))}
      </ul>
      <details>
        <summary>
          <T text={'What is checked — and what is not'} />
        </summary>
        <p>
          <T
            text={
              'Saved DNS email-record context, certificate trust/renewal and root HTTP/HTTPS configuration only. No malware, internal networks, account audit, exploitation or compliance certification.'
            }
          />
        </p>
        <p>{tr(limitations)}</p>
      </details>
    </section>
  );
}
