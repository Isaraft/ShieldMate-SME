import { T, tr } from '../i18n';
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
          {coverage.evaluated_scans}
          <T text={' evaluated source'} />{' '}
          <T text={coverage.evaluated_scans === 1 ? 'scan' : 'scans'} />
          <T text={' of '} /> {coverage.source_scans}
          <T text={' latest selected'} />{' '}
          <T text={coverage.source_scans === 1 ? 'scan' : 'scans'} />
          <T text={'. Last scan:'} /> {scanDate(coverage.last_scan_at)}.
        </p>
        <dl className="coverage-counts">
          {Object.entries(coverage.observation_counts).map(([key, value]) => (
            <div key={key}>
              <dt>{key.replaceAll('_', ' ')}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
        <p>{coverage.notes}</p>
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
          {coverage.in_flight_scans}
          <T text={' scans in progress;'} /> {coverage.pending_evaluations}
          <T
            text={
              ' terminal scans await offline evaluation. Existing findings retain their last known state. This page updates automatically.'
            }
          />
        </Alert>
      )}
      {coverage.unsupported_scans > 0 && (
        <Alert title={tr('Unsupported scan engine')} tone="warning">
          {coverage.unsupported_scans}
          <T text={' selected'} />{' '}
          <T
            text={coverage.unsupported_scans === 1 ? 'scan uses' : 'scans use'}
          />
          <T
            text={
              ' an unsupported observation version. Their rule evaluations remain unknown.'
            }
          />
        </Alert>
      )}
      {coverage.stale_assessments > 0 && (
        <Alert title={tr('Historical evidence')} tone="warning">
          {coverage.stale_assessments}
          <T text={' selected source'} />{' '}
          <T
            text={
              coverage.stale_assessments === 1
                ? 'assessment is'
                : 'assessments are'
            }
          />{' '}
          <T
            text={
              'stale. Their dates describe past observations, not a fresh security conclusion. Reverify ownership if needed before another scan.'
            }
          />
        </Alert>
      )}
    </>
  );
}
