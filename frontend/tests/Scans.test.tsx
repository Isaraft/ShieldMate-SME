import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, expect, it, vi } from 'vitest';
import { Scans } from '../src/pages/Scans';
import { Assets } from '../src/pages/Assets';

const scan = {
  id: 'scan-1',
  asset_id: 'asset',
  hostname: 'qa.example.com',
  status: 'completed',
  created_at: 1700000000,
  started_at: 1700000001,
  finished_at: 1700000002,
  completed_checks: 1,
  total_checks: 13,
  engine_version: 'starter-checks-1',
  error_code: null,
  observations: [
    {
      check_id: 'DNS_SPF_PRESENT',
      observed_at: 1700000001,
      outcome: 'attention',
      summary: 'No SPF record observed',
      source: 'DNS TXT',
      explanation: 'Limited observation only.',
      evidence: { record_count: 0, text: '<img src=x onerror=alert(1)>' },
    },
  ],
};
function show(path = '/app/assets/asset/scans/scan-1') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/app/assets" element={<Assets />} />
        <Route path="/app/assets/:domainId/scans" element={<Scans />} />
        <Route path="/app/assets/:domainId/scans/:scanId" element={<Scans />} />
        <Route path="/login" element={<p>Sign in again</p>} />
      </Routes>
    </MemoryRouter>,
  );
}
afterEach(() => vi.useRealTimers());
it('shows stored evidence as escaped text with outcome and limitations', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, json: async () => scan })),
  );
  const { container } = show();
  expect(await screen.findByText('No SPF record observed')).toBeInTheDocument();
  expect(screen.getByText('Needs attention')).toBeInTheDocument();
  await userEvent.click(screen.getByText('Technical evidence'));
  expect(screen.getByText('<img src=x onerror=alert(1)>')).toBeInTheDocument();
  expect(container.querySelector('img')).toBeNull();
});
it('polls active scans, then stops on terminal completion', async () => {
  vi.useFakeTimers();
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        ...scan,
        status: 'running',
        observations: [],
        completed_checks: 0,
        finished_at: null,
      }),
    })
    .mockResolvedValue({ ok: true, json: async () => scan });
  vi.stubGlobal('fetch', fetcher);
  show();
  await act(() => vi.advanceTimersByTimeAsync(0));
  expect(screen.getByText('running')).toBeInTheDocument();
  expect(screen.getAllByText(/Not checked/)).toHaveLength(3);
  await act(() => vi.advanceTimersByTimeAsync(2000));
  expect(screen.getByText('completed')).toBeInTheDocument();
  await act(() => vi.advanceTimersByTimeAsync(10000));
  expect(fetcher).toHaveBeenCalledTimes(2);
});
it('shows persistent history empty state and recoverable errors', async () => {
  const fetcher = vi
    .fn()
    .mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({}) })
    .mockResolvedValue({
      ok: true,
      json: async () => ({ items: [], total: 0, offset: 0, limit: 10 }),
    });
  vi.stubGlobal('fetch', fetcher);
  show('/app/assets/asset/scans');
  await userEvent.click(
    await screen.findByRole('button', { name: 'Retry loading scans' }),
  );
  expect(await screen.findByText('No completed scans yet')).toBeInTheDocument();
});
it('redirects an expired session without displaying evidence', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: false, status: 401, json: async () => ({}) })),
  );
  show();
  expect(await screen.findByText('Sign in again')).toBeInTheDocument();
  expect(screen.queryByText('No SPF record observed')).not.toBeInTheDocument();
});
it('starts an eligible scan through the CSRF API and opens its record', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options) => {
      const path = String(url);
      if (path.endsWith('/csrf'))
        return { ok: true, json: async () => ({ csrf_token: 'csrf' }) };
      if (path.endsWith('/domains'))
        return {
          ok: true,
          json: async () => [
            {
              id: 'asset',
              canonical_fqdn: 'qa.example.com',
              status: 'verified',
              scan_available: true,
              created_at: 1700000000,
              verification_valid_until: 9999999999,
            },
          ],
        };
      if (options?.method === 'POST')
        return { ok: true, json: async () => ({ id: 'scan-1' }) };
      return { ok: true, json: async () => scan };
    }),
  );
  show('/app/assets');
  await userEvent.click(
    await screen.findByRole('button', { name: 'Run security checks' }),
  );
  expect(
    await screen.findByRole('heading', { name: 'Security check record' }),
  ).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledWith(
    '/api/v1/domains/asset/scans',
    expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({ 'X-CSRF-Token': 'csrf' }),
    }),
  );
});
