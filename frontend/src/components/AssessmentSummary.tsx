import { T, tr, format } from '../i18n';
import type { FindingPage } from '../findingApi';
import { Alert } from './ui/Primitives';
import { scanDate } from '../scanApi';
const ruleLabels: Record<string, string> = {
  issue: 'supported issue conditions',
  clear: 'condition not observed',
  not_evaluable: 'unable to evaluate',
  not_applicable: 'insufficient applicable context',
};
export function AssessmentSummary({
  coverage,
  technical,
}: {
  coverage: FindingPage['summary']['assessment'];
  technical: boolean;
}) {
  return (
    <>
      <section
        className="assessment-summary"
        aria-labelledby="assessment-title"
      >
        <h2 id="assessment-title">
          <T text={'Limited external configuration assessment'} />
        </h2>
        <p>
          {format('assessment.sources', {
            evaluated: coverage.evaluated_scans,
            total: coverage.source_scans,
            date: scanDate(coverage.last_scan_at),
          })}
        </p>
        <dl className="coverage-counts">
          {Object.entries(coverage.observation_counts).map(([key, value]) => (
            <div key={key}>
              <dt>{tr(key)}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
        <p>{tr(coverage.notes)}</p>
        {technical && (
          <p>
            <T text={'Policy: '} />
            {coverage.policy_version}
          </p>
        )}
        <dl className="coverage-counts">
          {Object.entries(coverage.rule_counts).map(([key, value]) => (
            <div key={key}>
              <dt>
                <T text={'Rules: '} />
                {tr(ruleLabels[key] ?? key.replaceAll('_', ' '))}
              </dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </section>
      {(coverage.pending_evaluations > 0 || coverage.in_flight_scans > 0) && (
        <Alert title={tr('Assessment still processing')}>
          {format('assessment.processing', {
            running: coverage.in_flight_scans,
            pending: coverage.pending_evaluations,
          })}
        </Alert>
      )}
      {coverage.unsupported_scans > 0 && (
        <Alert title={tr('Unsupported scan engine')} tone="warning">
          {format('assessment.unsupported', {
            count: coverage.unsupported_scans,
          })}
        </Alert>
      )}
      {coverage.stale_assessments > 0 && (
        <Alert title={tr('Historical evidence')} tone="warning">
          {format('assessment.stale', { count: coverage.stale_assessments })}
        </Alert>
      )}
    </>
  );
}
