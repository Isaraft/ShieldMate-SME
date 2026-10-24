import { ApiError } from './authApi';
import type { Finding } from './findingApi';
import type { Locale } from './i18n';
export type ReportAsset = {
  id: string;
  hostname: string;
  currently_authorized: boolean;
  verification_valid_until: number | null;
  assessed: boolean;
  reason: string;
  stale: boolean;
  scan_id: string | null;
  scan_status: string | null;
  scan_finished_at: number | null;
  observation_counts: Record<string, number>;
  observations: {
    id: string;
    check_id: string;
    outcome: string;
    observed_at: number;
    values: Record<string, string | number>;
  }[];
};
export type ReportTask = {
  id: string;
  finding_id: string;
  title: string;
  hostname: string;
  status: string;
  owner_label: string;
  updated_at: number;
  completed_at: number | null;
  finding_status: string;
  finding_stale: boolean;
  recommendation: string;
};
export type Snapshot = {
  schema_version: string;
  id: string;
  kind: 'real' | 'demo';
  organization_id: string;
  organization_name: string;
  created_at: number;
  locale: Locale;
  policy_version: string;
  readiness: string;
  can_generate: boolean;
  counts: Record<string, number>;
  finding_counts: Record<string, number>;
  task_counts: Record<string, number>;
  assets: ReportAsset[];
  findings: Finding[];
  priorities: Finding[];
  tasks: ReportTask[];
};
export type ReportMeta = {
  id: string;
  locale: Locale;
  created_at: number;
  status: 'generating' | 'ready' | 'failed';
  schema_version: string;
  byte_count: number;
  sha256: string | null;
  error_code: string | null;
};
export type ReportHistory = {
  items: ReportMeta[];
  total: number;
  offset: number;
  limit: number;
};
export async function downloadPdf(url: string, filename: string) {
  const response = await fetch('/api/v1' + url, {
    credentials: url.startsWith('/demo/') ? 'omit' : 'include',
  });
  if (!response.ok)
    throw new ApiError(
      response.status === 401
        ? 'Your session has ended. Sign in again.'
        : 'Unable to download PDF. Retry.',
      response.status,
    );
  const blob = await response.blob();
  if (blob.type !== 'application/pdf')
    throw new Error('The report is unavailable.');
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}
