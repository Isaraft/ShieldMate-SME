import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, expect, it, vi } from 'vitest';
import { Findings } from '../src/pages/Findings';
import { FindingDetail } from '../src/pages/FindingDetail';
import type { Finding, FindingPage } from '../src/findingApi';

const finding: Finding = {
  id: 'fixture',
  asset_id: 'asset',
  hostname: 'qa.example.com',
  fingerprint: 'stable',
  rule_id: 'TLS_CERTIFICATE_ACTION',
  policy_version: 'starter-risk-1',
  category: 'tls',
  status: 'open',
  severity: 'high',
  urgency: 2,
  relevance: 2,
  confidence: 'conclusive',
  title: 'Certificate renewal was due within 7 days',
  impact: 'Certificate expiry can interrupt access.',
  recommendation:
    'Check renewal, install the renewed certificate, then rerun authorized checks.',
  rationale: 'A recorded near-term certificate deadline.',
  limitation: 'Only one endpoint was observed.',
  first_seen_at: 1700000000,
  last_seen_at: 1700000000,
  observed_at: 1700000000,
  resolved_at: null,
  last_evaluation_at: 1700000001,
  recheck_status: 'confirmed',
  stale: false,
  history_truncated: false,
  source_scan_id: 'source',
  source_scan_available: true,
  ranking_reason: 'High, urgency 2/3. Stable ordering, not a score.',
  evidence: [
    {
      observation_id: 'observation',
      check_id: 'TLS_CERTIFICATE',
      observed_at: 1700000000,
      outcome: 'pass',
      source: 'TLS 443',
      values: { not_after: 1700600000, text: '<script>alert(1)</script>' },
    },
  ],
};
function page(): FindingPage {
  return {
    domains: [{ id: 'asset', hostname: 'qa.example.com' }],
    items: [finding],
    priorities: [finding],
    total: 1,
    offset: 0,
    limit: 20,
    summary: {
      total: 1,
      counts_by_status: { open: 1 },
      counts_by_severity: { high: 1 },
      counts_by_category: { tls: 1 },
      assessment: {
        policy_version: 'starter-risk-1',
        source_scans: 1,
        evaluated_scans: 1,
        pending_evaluations: 0,
        in_flight_scans: 0,
        stale_assessments: 0,
        unsupported_scans: 0,
        observation_counts: { pass: 1, not_checked: 12 },
        rule_counts: { issue: 1, not_evaluable: 5 },
        last_scan_at: 1700000000,
        notes: 'Limited saved observations only. No numerical score.',
      },
    },
  };
}
function show(path = '/app/findings') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/app/findings" element={<Findings />} />
        <Route path="/app/findings/:findingId" element={<FindingDetail />} />
        <Route path="/login" element={<p>Sign in again</p>} />
      </Routes>
    </MemoryRouter>,
  );
}
afterEach(() => vi.useRealTimers());
it('renders actual server priorities and counts without filling missing top-three slots', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, json: async () => page() })),
  );
  show();
  expect(
    await screen.findByText(
      '1 finding in this selection · 1 open · 0 resolved.',
    ),
  ).toBeInTheDocument();
  expect(screen.getByText('Priority 1 / qa.example.com')).toBeInTheDocument();
  expect(screen.queryByText(/Priority 2/)).not.toBeInTheDocument();
  expect(screen.getByText('Recommended next step')).toBeInTheDocument();
});
it('applies functional typed filters and preserves source-scan context', async () => {
  const fetcher = vi.fn(async () => ({ ok: true, json: async () => page() }));
  vi.stubGlobal('fetch', fetcher);
  show('/app/findings?scan_id=source');
  await screen.findByRole('combobox', { name: 'Status' });
  await userEvent.selectOptions(
    screen.getByRole('combobox', { name: 'Status' }),
    'resolved',
  );
  await userEvent.selectOptions(
    screen.getByRole('combobox', { name: 'Category' }),
    'tls',
  );
  await userEvent.click(screen.getByRole('button', { name: 'Apply filters' }));
  expect(fetcher).toHaveBeenLastCalledWith(
    expect.stringMatching(/status=resolved.*category=tls.*scan_id=source/),
    expect.anything(),
  );
});
it('changes presentation without changing server truth or exposing executable evidence', async () => {
  const fetcher = vi.fn(async () => ({ ok: true, json: async () => page() }));
  vi.stubGlobal('fetch', fetcher);
  const { container } = show();
  await screen.findByText('Priority 1 / qa.example.com');
  await userEvent.click(screen.getByRole('radio', { name: 'Technical' }));
  await userEvent.click(screen.getByText('Verifiable evidence'));
  expect(screen.getByText('<script>alert(1)</script>')).toBeInTheDocument();
  expect(container.querySelector('script')).toBeNull();
  expect(fetcher).toHaveBeenCalledTimes(1);
});
it('distinguishes no scans from insufficient assessment evidence', async () => {
  const data = page();
  data.items = [];
  data.priorities = [];
  data.total = 0;
  data.summary.assessment.source_scans = 0;
  data.summary.assessment.evaluated_scans = 0;
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, json: async () => data })),
  );
  show();
  expect(await screen.findByText('No assessments yet')).toBeInTheDocument();
  expect(screen.queryByText('Secure')).not.toBeInTheDocument();
});
it('shows stale and not-rechecked annotations separately from resolution', async () => {
  const data = page();
  data.items = [{ ...finding, stale: true, recheck_status: 'not_rechecked' }];
  data.priorities = [];
  data.summary.assessment.stale_assessments = 1;
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, json: async () => data })),
  );
  show();
  expect(
    await screen.findByText('Historical evidence — stale'),
  ).toBeInTheDocument();
  expect(
    screen.getByText('Not rechecked', { selector: 'span' }),
  ).toBeInTheDocument();
  expect(screen.getByText('open · high')).toBeInTheDocument();
});
it('polls pending evaluation and stops after terminal assessment', async () => {
  vi.useFakeTimers();
  const pending = page();
  pending.summary.assessment.pending_evaluations = 1;
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce({ ok: true, json: async () => pending })
    .mockResolvedValue({ ok: true, json: async () => page() });
  vi.stubGlobal('fetch', fetcher);
  show();
  await act(() => vi.advanceTimersByTimeAsync(0));
  expect(screen.getByText('Assessment still processing')).toBeInTheDocument();
  await act(() => vi.advanceTimersByTimeAsync(3000));
  expect(
    screen.queryByText('Assessment still processing'),
  ).not.toBeInTheDocument();
  await act(() => vi.advanceTimersByTimeAsync(9000));
  expect(fetcher).toHaveBeenCalledTimes(2);
});
it('handles API failure and recovers through retry', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({}) })
      .mockResolvedValue({ ok: true, json: async () => page() }),
  );
  show();
  await userEvent.click(
    await screen.findByRole('button', { name: 'Retry findings' }),
  );
  expect(
    await screen.findByText('Priority 1 / qa.example.com'),
  ).toBeInTheDocument();
});
it('does not show private data after session expiry', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: false, status: 401, json: async () => ({}) })),
  );
  show();
  expect(await screen.findByText('Sign in again')).toBeInTheDocument();
  expect(screen.queryByText(finding.title)).not.toBeInTheDocument();
});
it('shows resolution/reopening history and preserved evidence after source retention', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        ...finding,
        status: 'resolved',
        resolved_at: 1700100000,
        source_scan_available: false,
        history: [
          {
            kind: 'resolved',
            source_scan_id: 'source',
            source_scan_available: false,
            occurred_at: 1700100000,
            policy_version: 'starter-risk-1',
            snapshot: {
              rule_id: finding.rule_id,
              policy_version: 'starter-risk-1',
              decision: 'clear',
              reason: 'Comparable source evidence.',
              severity: 'high',
              title: finding.title,
              evidence: finding.evidence,
            },
          },
        ],
      }),
    })),
  );
  show('/app/findings/fixture');
  expect(
    await screen.findByText('Resolved by comparable technical evidence'),
  ).toBeInTheDocument();
  expect(screen.getByText(/Source scan was pruned/)).toBeInTheDocument();
  expect(screen.getByText('Finding history')).toBeInTheDocument();
  expect(
    screen.getByText(/Only a later conclusive authorized check/),
  ).toBeInTheDocument();
});
