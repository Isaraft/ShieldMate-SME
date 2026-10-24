import { dateTime } from './i18n';
export type ScanState =
  'queued' | 'running' | 'completed' | 'partial' | 'failed' | 'interrupted';
export type Observation = {
  check_id: string;
  observed_at: number;
  outcome: 'pass' | 'attention' | 'informational' | 'inconclusive' | 'error';
  summary: string;
  source: string;
  explanation: string;
  evidence: Record<string, string | number | string[]>;
};
export type Scan = {
  id: string;
  asset_id: string;
  hostname: string;
  status: ScanState;
  created_at: number;
  started_at: number | null;
  finished_at: number | null;
  completed_checks: number;
  total_checks: number;
  engine_version: string;
  error_code: string | null;
};
export type ScanDetail = Scan & { observations: Observation[] };
export type History = {
  items: Scan[];
  offset: number;
  limit: number;
  total: number;
};
export const isActive = (state: ScanState) =>
  state === 'queued' || state === 'running';
export function scanDate(value: number | null) {
  return dateTime(value);
}
export const scanErrors: Record<string, string> = {
  authorization_changed:
    'Authorization or DNS proof changed. Verify the domain again before starting another scan.',
  unsafe_destination:
    'DNS includes a private or special-use address. Network probes were blocked.',
  no_public_addresses:
    'No public destination was available. Network probes were blocked.',
  worker_interrupted:
    'The worker stopped before completion. Recorded observations remain; you may start another scan.',
  queue_expired:
    'The job waited too long for a worker and did not run. Check the local worker service.',
  overall_timeout:
    'The scan reached its time budget. Recorded observations remain available.',
  checks_incomplete:
    'Some checks were inconclusive. Review each observation for its reason.',
};
