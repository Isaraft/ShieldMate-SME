export type Evidence = {
  observation_id: string;
  check_id: string;
  observed_at: number;
  outcome: string;
  source: string;
  values: Record<string, string | number>;
};
export type Finding = {
  id: string;
  asset_id: string;
  hostname: string;
  fingerprint: string;
  rule_id: string;
  policy_version: string;
  category: string;
  status: 'open' | 'resolved';
  severity: 'high' | 'medium' | 'low' | 'info';
  urgency: number;
  relevance: number;
  confidence: string;
  title: string;
  impact: string;
  recommendation: string;
  rationale: string;
  limitation: string;
  first_seen_at: number;
  last_seen_at: number;
  resolved_at: number | null;
  observed_at: number;
  last_evaluation_at: number;
  recheck_status: string;
  stale: boolean;
  history_truncated: boolean;
  source_scan_id: string;
  source_scan_available: boolean;
  evidence: Evidence[];
  task_id?: string | null;
  task_status?: string | null;
  ranking_reason: string;
};
export type RuleEvaluation = {
  rule_id: string;
  policy_version: string;
  decision: string;
  reason: string;
  severity: string;
  title: string;
  evidence: Evidence[];
};
export type FindingDetail = Finding & {
  history: {
    kind: string;
    source_scan_id: string;
    source_scan_available: boolean;
    policy_version: string;
    occurred_at: number;
    snapshot: RuleEvaluation;
  }[];
};
export type FindingPage = {
  domains: { id: string; hostname: string }[];
  items: Finding[];
  priorities: Finding[];
  total: number;
  offset: number;
  limit: number;
  summary: {
    total: number;
    counts_by_status: Record<string, number>;
    counts_by_severity: Record<string, number>;
    counts_by_category: Record<string, number>;
    assessment: {
      policy_version: string;
      source_scans: number;
      evaluated_scans: number;
      pending_evaluations: number;
      in_flight_scans: number;
      stale_assessments: number;
      unsupported_scans: number;
      observation_counts: Record<string, number>;
      rule_counts: Record<string, number>;
      last_scan_at: number | null;
      notes: string;
    };
  };
};
