import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { Reports } from '../src/pages/Reports';
import { Demo } from '../src/pages/Demo';
import { App } from '../src/App';
import { LanguageSwitch, setLocale, tr, dateTime } from '../src/i18n';
import type { Snapshot, ReportMeta } from '../src/reportApi';
import { finding } from './fixtures/workflow';

const overview: Snapshot = {
  schema_version: 'security-snapshot-1',
  id: 'preview',
  kind: 'real',
  organization_id: 'org',
  organization_name: 'QA company',
  created_at: 1790812920,
  locale: 'en',
  policy_version: 'starter-risk-1',
  readiness: 'ready',
  can_generate: true,
  counts: {
    enrolled_domains: 1,
    authorized_domains: 1,
    assessed_domains: 1,
    without_usable_evidence: 0,
    excluded_historical_findings: 0,
  },
  finding_counts: { 'open:high': 1 },
  task_counts: { done: 1 },
  assets: [],
  findings: [finding],
  priorities: [finding],
  tasks: [],
};
const meta: ReportMeta = {
  id: 'report-id',
  locale: 'en',
  created_at: 1790812920,
  status: 'ready',
  schema_version: 'security-snapshot-1',
  byte_count: 12000,
  sha256: 'abc123',
  error_code: null,
};
function response(value: unknown, status = 200) {
  return { ok: status < 400, status, json: async () => value };
}
function showReports() {
  render(
    <MemoryRouter initialEntries={['/app/reports']}>
      <LanguageSwitch />
      <Routes>
        <Route path="/app/reports" element={<Reports />} />
        <Route path="/login" element={<p>Login required</p>} />
      </Routes>
    </MemoryRouter>,
  );
}
beforeEach(() => {
  setLocale('en');
  window.localStorage.clear();
});
afterEach(() => {
  act(() => setLocale('en'));
  window.localStorage.clear();
});
function transport(current = overview, items: ReportMeta[] = []) {
  return vi.fn(async (url, options) => {
    if (String(url).endsWith('/csrf'))
      return response({ csrf_token: 'csrf-test' });
    if (String(url).endsWith('/overview')) return response(current);
    if (options?.method === 'POST') {
      items.push(meta);
      return response(meta);
    }
    return response({ items, total: items.length, offset: 0, limit: 10 });
  });
}
it('shows actual assessed scope and generates through a session-bound CSRF request', async () => {
  const fetcher = transport();
  vi.stubGlobal('fetch', fetcher);
  showReports();
  await screen.findByText('Ready', { exact: true });
  await userEvent.click(
    screen.getByRole('button', { name: 'Generate PDF Snapshot' }),
  );
  await screen.findByText('PDF snapshot saved. Download it from history.');
  await screen.findByRole('button', { name: 'Download PDF' });
  expect(fetcher).toHaveBeenCalledWith(
    '/api/v1/reports',
    expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({ 'X-CSRF-Token': 'csrf-test' }),
      body: expect.stringContaining('"locale":"en"'),
    }),
  );
  expect(
    screen.getByText(
      'Human task status does not determine finding resolution.',
    ),
  ).toBeInTheDocument();
});
it.each(['no_assets', 'unverified', 'no_evidence', 'processing'])(
  'disables generation for %s without inventing a report',
  async (readiness) => {
    vi.stubGlobal(
      'fetch',
      transport({
        ...overview,
        readiness,
        can_generate: false,
        priorities: [],
        findings: [],
      }),
    );
    showReports();
    await screen.findByText('No qualifying report data');
    expect(
      screen.getByRole('button', { name: 'Generate PDF Snapshot' }),
    ).toBeDisabled();
    expect(screen.getByText('No saved snapshots yet.')).toBeInTheDocument();
  },
);
it('keeps incomplete/stale evidence visible with its actual scope', async () => {
  vi.stubGlobal(
    'fetch',
    transport({
      ...overview,
      readiness: 'stale',
      counts: { ...overview.counts, excluded_historical_findings: 3 },
    }),
  );
  showReports();
  await screen.findByText('Stale', { exact: true });
  expect(
    screen.getByText(/3 historical findings excluded/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole('button', { name: 'Generate PDF Snapshot' }),
  ).toBeEnabled();
});
it('handles a failed generation without publishing a working download', async () => {
  const fetcher = transport();
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options) =>
      options?.method === 'POST'
        ? response({ ...meta, status: 'failed', sha256: null, byte_count: 0 })
        : fetcher(url, options),
    ),
  );
  showReports();
  await screen.findByRole('button', { name: 'Generate PDF Snapshot' });
  await userEvent.click(
    screen.getByRole('button', { name: 'Generate PDF Snapshot' }),
  );
  await screen.findByText(
    'PDF generation failed. No broken document was published. Retry with a new attempt.',
  );
  expect(
    screen.queryByRole('button', { name: 'Download PDF' }),
  ).not.toBeInTheDocument();
});
it('retries read errors and redirects an expired report session', async () => {
  let expired = false;
  vi.stubGlobal(
    'fetch',
    vi.fn(async () =>
      response(
        {
          error: {
            message: expired ? 'Session ended' : 'Connection unavailable',
          },
        },
        expired ? 401 : 503,
      ),
    ),
  );
  showReports();
  await screen.findByText('Reports unavailable');
  expired = true;
  await userEvent.click(screen.getByRole('button', { name: 'Retry reports' }));
  await screen.findByText('Login required');
});
it('downloads only the authenticated artifact route and revokes its local blob URL', async () => {
  const create = vi.fn(() => 'blob:qa'),
    revoke = vi.fn();
  vi.stubGlobal(
    'URL',
    class extends URL {
      static createObjectURL = create;
      static revokeObjectURL = revoke;
    },
  );
  const click = vi
    .spyOn(HTMLAnchorElement.prototype, 'click')
    .mockImplementation(() => {});
  const fetcher = transport(overview, [meta]);
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options) =>
      String(url).includes('/download')
        ? {
            ok: true,
            status: 200,
            blob: async () =>
              new Blob(['%PDF-QA'], { type: 'application/pdf' }),
          }
        : fetcher(url, options),
    ),
  );
  showReports();
  await screen.findByRole('button', { name: 'Download PDF' });
  await userEvent.click(screen.getByRole('button', { name: 'Download PDF' }));
  await screen.findByText(
    'PDF download started. This saved artifact will not change.',
  );
  expect(fetch).toHaveBeenCalledWith(
    '/api/v1/reports/report-id/download',
    expect.objectContaining({ credentials: 'include' }),
  );
  expect(create).toHaveBeenCalled();
  expect(click).toHaveBeenCalled();
  await waitFor(() => expect(revoke).toHaveBeenCalledWith('blob:qa'), {
    timeout: 2000,
  });
  click.mockRestore();
});
it('switches report language without losing route or data', async () => {
  const fetcher = transport();
  vi.stubGlobal('fetch', fetcher);
  showReports();
  await screen.findByRole('button', { name: 'Generate PDF Snapshot' });
  await userEvent.click(screen.getByRole('button', { name: 'Русский' }));
  expect(document.documentElement.lang).toBe('ru');
  expect(
    screen.getByRole('heading', { name: 'Отчёты о безопасности' }),
  ).toBeInTheDocument();
  expect(
    screen.getByRole('button', { name: 'Создать PDF-отчёт' }),
  ).toBeEnabled();
  await userEvent.click(
    screen.getByRole('button', { name: 'Создать PDF-отчёт' }),
  );
  await screen.findByText(
    'PDF-отчёт сохранён. Скачайте его из списка отчётов.',
  );
  expect(fetcher).toHaveBeenCalledWith(
    '/api/v1/reports',
    expect.objectContaining({ body: expect.stringContaining('"locale":"ru"') }),
  );
});
it('preserves entered account values while localizing global navigation and form labels', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () =>
      response({ error: { message: 'Sign in to continue' } }, 401),
    ),
  );
  render(
    <MemoryRouter initialEntries={['/login']}>
      <App />
    </MemoryRouter>,
  );
  await userEvent.type(
    screen.getByRole('textbox', { name: 'Email address' }),
    'owner@example.com',
  );
  await userEvent.type(
    screen.getByLabelText('Password', { exact: true }),
    'A valid password for QA',
  );
  await userEvent.click(screen.getByRole('button', { name: 'Русский' }));
  expect(
    screen.getByRole('textbox', { name: 'Электронная почта' }),
  ).toHaveValue('owner@example.com');
  expect(screen.getByLabelText('Пароль', { exact: true })).toHaveValue(
    'A valid password for QA',
  );
  expect(window.localStorage.getItem('shieldmate-language')).toBe('ru');
  expect(window.localStorage.length).toBe(1);
});
it('has deterministic fallback and historical timezone formatting', () => {
  expect(tr('not-in-the-catalog', 'ru')).toBe('not-in-the-catalog');
  expect(tr('Sign in', 'ru')).toBe('Войти');
  expect(dateTime(1700000000)).toContain('GMT+6');
  expect(dateTime(1790812800)).toContain('GMT+5');
});
it('keeps demo data labeled and never requests authenticated customer endpoints', async () => {
  const data = {
    ...overview,
    id: 'demo',
    kind: 'demo',
    organization_name: 'Sample Merchant KZ',
    can_generate: false,
  };
  const fetcher = vi.fn(async (url: unknown) => {
    expect(String(url)).toContain('/demo?');
    return response(data);
  });
  vi.stubGlobal('fetch', fetcher);
  render(
    <MemoryRouter>
      <Demo />
    </MemoryRouter>,
  );
  await screen.findByText(/Sample Merchant KZ/);
  await userEvent.click(
    screen.getByRole('button', { name: '2. Findings and priorities' }),
  );
  expect(screen.getByText(finding.title)).toBeInTheDocument();
  expect(
    screen.getAllByText('SAMPLE DATA / DEMO — NOT A LIVE ASSESSMENT'),
  ).toHaveLength(2);
  expect(
    fetcher.mock.calls.every((call) =>
      String(call[0]).startsWith('/api/v1/demo?'),
    ),
  ).toBe(true);
  await userEvent.click(screen.getByRole('button', { name: '4. Sample PDF' }));
  expect(
    screen.getByRole('button', { name: 'Download DEMO PDF' }),
  ).toBeInTheDocument();
});
it('renders loading without fake security figures', () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => new Promise(() => {})),
  );
  showReports();
  expect(screen.getByText('Loading report readiness…')).toBeInTheDocument();
  expect(screen.queryByText('Enrolled domains')).not.toBeInTheDocument();
});
