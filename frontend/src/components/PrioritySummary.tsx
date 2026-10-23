import { TaskAction } from './TaskAction';
import { Link } from 'react-router-dom';
import type { Finding } from '../findingApi';
import { FindingState, EvidenceList } from './FindingEvidence';
import { scanDate } from '../scanApi';
export function PrioritySummary({
  findings,
  technical,
}: {
  findings: Finding[];
  technical: boolean;
}) {
  return (
    <section className="priority-section" aria-labelledby="priorities-title">
      <h2 id="priorities-title">Top priorities in this selection</h2>
      <p>
        Ranked by severity, urgency, observed relevance, confidence, evidence
        time and stable fingerprint. Fewer than three means fewer supported open
        priorities.
      </p>
      {findings.length ? (
        <ol className="priority-list">
          {findings.map((finding, index) => (
            <li key={finding.id}>
              <p className="eyebrow">
                Priority {index + 1} / {finding.hostname}
              </p>
              <h3>
                <Link to={`/app/findings/${finding.id}`}>{finding.title}</Link>
              </h3>
              <FindingState finding={finding} />
              <TaskAction finding={finding} />
              <h4>Why this matters</h4>
              <p>{finding.impact}</p>
              <h4>Recommended next step</h4>
              <p>{finding.recommendation}</p>
              <p className="field-help">
                Last observed {scanDate(finding.last_seen_at)} ·{' '}
                {finding.rule_id}
              </p>
              {technical && (
                <>
                  <p>{finding.rationale}</p>
                  <p>{finding.ranking_reason}</p>
                  <details>
                    <summary>Verifiable evidence</summary>
                    <EvidenceList evidence={finding.evidence} />
                  </details>
                </>
              )}
            </li>
          ))}
        </ol>
      ) : (
        <p>
          No supported open priorities in this selection. This is not a
          declaration that the company is secure.
        </p>
      )}
    </section>
  );
}
