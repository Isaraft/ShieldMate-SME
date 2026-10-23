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
        <h2 id="assessment-title">Limited external configuration assessment</h2>
        <p>
          {coverage.evaluated_scans} evaluated source{' '}
          {coverage.evaluated_scans === 1 ? 'scan' : 'scans'} of{' '}
          {coverage.source_scans} latest selected{' '}
          {coverage.source_scans === 1 ? 'scan' : 'scans'}. Last scan:{' '}
          {scanDate(coverage.last_scan_at)}.
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
        {technical && <p>Policy: {coverage.policy_version}</p>}
        <dl className="coverage-counts">
          {Object.entries(coverage.rule_counts).map(([key, value]) => (
            <div key={key}>
              <dt>Rules: {ruleLabels[key] ?? key.replaceAll('_', ' ')}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </section>
      {(coverage.pending_evaluations > 0 || coverage.in_flight_scans > 0) && (
        <Alert title="Assessment still processing">
          {coverage.in_flight_scans} scans in progress;{' '}
          {coverage.pending_evaluations} terminal scans await offline
          evaluation. Existing findings retain their last known state. This page
          updates automatically.
        </Alert>
      )}
      {coverage.unsupported_scans > 0 && (
        <Alert title="Unsupported scan engine" tone="warning">
          {coverage.unsupported_scans} selected{' '}
          {coverage.unsupported_scans === 1 ? 'scan uses' : 'scans use'} an
          unsupported observation version. Their rule evaluations remain
          unknown.
        </Alert>
      )}
      {coverage.stale_assessments > 0 && (
        <Alert title="Historical evidence" tone="warning">
          {coverage.stale_assessments} selected source{' '}
          {coverage.stale_assessments === 1
            ? 'assessment is'
            : 'assessments are'}{' '}
          stale. Their dates describe past observations, not a fresh security
          conclusion. Reverify ownership if needed before another scan.
        </Alert>
      )}
    </>
  );
}
