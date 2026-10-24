import { T, tr, localeName } from '../i18n';
import { Link } from 'react-router-dom';
import type { Evidence, Finding } from '../findingApi';
import { Badge } from './ui/Primitives';
import { scanDate } from '../scanApi';

export function FindingState({ finding }: { finding: Finding }) {
  return (
    <div className="finding-state">
      <Badge
        tone={
          finding.status === 'resolved'
            ? 'success'
            : finding.severity === 'high'
              ? 'error'
              : 'neutral'
        }
      >
        {tr(finding.status)} · {tr(finding.severity)}
      </Badge>
      {finding.stale && (
        <Badge tone="warning">
          <T text={'Historical evidence — stale'} />
        </Badge>
      )}
      {finding.recheck_status === 'not_rechecked' && (
        <Badge tone="warning">
          <T text={'Not rechecked'} />
        </Badge>
      )}
    </div>
  );
}
export function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  return (
    <div className="finding-evidence">
      {evidence.map((item) => (
        <section key={item.observation_id}>
          <h3>{item.check_id}</h3>
          <p>
            {item.source} · {scanDate(item.observed_at)}
            <T text={' · Collection outcome:'} /> {tr(item.outcome)}
          </p>
          <dl>
            {Object.entries(item.values).map(([key, value]) => (
              <div key={key}>
                <dt>{key.replaceAll('_', ' ')}</dt>
                <dd>
                  {typeof value === 'number' &&
                  ['not_before', 'not_after'].includes(key) ? (
                    <>
                      <time dateTime={new Date(value * 1000).toISOString()}>
                        {new Date(value * 1000).toLocaleString(localeName(), {
                          timeZone: 'Asia/Almaty',
                          timeZoneName: 'short',
                        })}
                      </time>
                      <br />
                      <code>
                        <T text={'UTC epoch '} />
                        {value}
                      </code>
                    </>
                  ) : (
                    <code>{String(value)}</code>
                  )}
                </dd>
              </div>
            ))}
          </dl>
          <p className="field-help">
            <T text={'Observation ID: '} />
            {item.observation_id}
          </p>
        </section>
      ))}
    </div>
  );
}
export function SourceLink({ finding }: { finding: Finding }) {
  return finding.source_scan_available ? (
    <Link
      to={`/app/assets/${finding.asset_id}/scans/${finding.source_scan_id}`}
    >
      <T text={'Open source scan'} />
    </Link>
  ) : (
    <p>
      <T
        text={
          'Source scan was pruned under retention. The saved evidence snapshot remains available.'
        }
      />
    </p>
  );
}
