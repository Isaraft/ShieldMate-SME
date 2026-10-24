import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, expect, it, vi } from 'vitest';
import { App } from '../src/App';
import { FindingFilters } from '../src/components/FindingFilters';
import { Tasks } from '../src/pages/Tasks';
import {
  LanguageSwitch,
  setLocale,
  tr,
  format,
  type Locale,
} from '../src/i18n';
import { finding } from './fixtures/workflow';
import english from '../../backend/app/locales/en.json';
import russian from '../../backend/app/locales/ru.json';
import kazakh from '../../backend/app/locales/kk.json';

afterEach(() => act(() => setLocale('en')));
function respond(data: unknown) {
  return { ok: true, status: 200, json: async () => data };
}
it.each(['en', 'ru', 'kk'] as Locale[])(
  'keeps canonical filter values in %s',
  async (locale) => {
    setLocale(locale);
    render(
      <MemoryRouter>
        <FindingFilters
          domains={[{ id: 'asset', hostname: 'qa.example.com' }]}
        />
      </MemoryRouter>,
    );
    const options = screen.getAllByRole('option');
    expect(options.some((o) => o.getAttribute('value') === 'high')).toBe(true);
    expect(options.some((o) => o.getAttribute('value') === 'tls')).toBe(true);
    expect(options.some((o) => o.getAttribute('value') === 'open')).toBe(true);
    expect(
      options.every(
        (o) =>
          !/[А-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІі]/.test(o.getAttribute('value') ?? ''),
      ),
    ).toBe(true);
  },
);
it.each(['en', 'ru', 'kk'] as Locale[])(
  'submits task severity as a canonical API value in %s',
  async (locale) => {
    setLocale(locale);
    const fetcher = vi.fn(async () =>
      respond({ items: [], total: 0, offset: 0, limit: 20, domains: [] }),
    );
    vi.stubGlobal('fetch', fetcher);
    render(
      <MemoryRouter initialEntries={['/app/tasks']}>
        <Routes>
          <Route path="/app/tasks" element={<Tasks />} />
        </Routes>
      </MemoryRouter>,
    );
    const severity = await screen.findByRole('combobox', {
      name: tr('Finding priority'),
    });
    await userEvent.selectOptions(severity, 'high');
    await userEvent.click(
      screen.getByRole('button', { name: tr('Apply task filters') }),
    );
    await waitFor(() =>
      expect(fetcher).toHaveBeenCalledWith(
        '/api/v1/tasks?severity=high&sort=updated',
        expect.anything(),
      ),
    );
  },
);
it('has exact key and named-placeholder parity in all catalogs', () => {
  const fields = (s: string) =>
    [...s.matchAll(/\{([a-zA-Z_]+)\}/g)].map((m) => m[1]).sort();
  for (const catalog of [russian, kazakh]) {
    expect(Object.keys(catalog).sort()).toEqual(Object.keys(english).sort());
    for (const key of Object.keys(english) as (keyof typeof english)[]) {
      expect(catalog[key].trim()).not.toBe('');
      expect(fields(catalog[key])).toEqual(fields(english[key]));
    }
  }
});
it('uses natural full messages, deterministic fallback and preserves raw values', () => {
  setLocale('kk');
  expect(format('task.selection.one', { count: 1 })).toBe(
    'Іріктеудегі сақталған тапсырмалар: 1.',
  );
  expect(tr('not-a-catalog-key')).toBe('not-a-catalog-key');
  expect(tr('merchant.example')).toBe('merchant.example');
  expect(tr(finding.title)).toContain('сертификатты');
  setLocale('unknown' as Locale);
  expect(document.documentElement.lang).toBe('en');
});
it('switches EN/RU/KK without losing entered credentials or route', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: false,
      status: 401,
      json: async () => ({ error: { message: 'Sign in to continue' } }),
    })),
  );
  render(
    <MemoryRouter initialEntries={['/login']}>
      <App />
    </MemoryRouter>,
  );
  await userEvent.type(
    screen.getByRole('textbox', { name: 'Email address' }),
    'qa@example.com',
  );
  await userEvent.type(
    screen.getByLabelText('Password', { exact: true }),
    'QA password unchanged',
  );
  for (const name of ['Қазақша', 'Русский', 'English']) {
    await userEvent.click(screen.getByRole('button', { name }));
    expect(
      screen.getByRole('textbox', { name: tr('Email address') }),
    ).toHaveValue('qa@example.com');
    expect(screen.getByLabelText(tr('Password'), { exact: true })).toHaveValue(
      'QA password unchanged',
    );
    expect(document.documentElement.lang).toBe(
      name === 'Қазақша' ? 'kk' : name === 'Русский' ? 'ru' : 'en',
    );
  }
});
it('keeps keyboard focus on the language selector on anchored routes', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: false, status: 401, json: async () => null })),
  );
  render(
    <MemoryRouter initialEntries={['/#how-it-works']}>
      <App />
    </MemoryRouter>,
  );
  const toggle = screen.getByRole('button', { name: 'Қазақша' });
  await userEvent.click(toggle);
  expect(toggle).toHaveFocus();
  expect(document.documentElement.lang).toBe('kk');
});
it('shows all three native language names with pressed-state semantics', () => {
  setLocale('kk');
  render(<LanguageSwitch />);
  expect(screen.getByRole('button', { name: 'Қазақша' })).toHaveAttribute(
    'aria-pressed',
    'true',
  );
  expect(screen.getByRole('button', { name: 'English' })).toHaveAttribute(
    'aria-pressed',
    'false',
  );
});

it.each(['en', 'ru', 'kk'] as Locale[])(
  'localizes the API-provided finding heading in %s without changing its hostname',
  async (locale) => {
    act(() => setLocale(locale));
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          respond({ ...finding, history: [], history_truncated: false }),
        ),
    );
    const { FindingDetail } = await import('../src/pages/FindingDetail');
    render(
      <MemoryRouter initialEntries={['/app/findings/fixture']}>
        <Routes>
          <Route path="/app/findings/:findingId" element={<FindingDetail />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(
      await screen.findByRole('heading', { level: 1, name: tr(finding.title) }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(finding.hostname, { exact: true }),
    ).toBeInTheDocument();
    if (locale !== 'en')
      expect(
        screen.queryByRole('heading', { name: finding.title }),
      ).not.toBeInTheDocument();
  },
);

it('uses a readable numeric Kazakh date without an ICU M10 month fallback', async () => {
  act(() => setLocale('kk'));
  const { dateTime } = await import('../src/i18n');
  const value = dateTime(Date.UTC(2026, 9, 24, 0, 0) / 1000);
  expect(value).not.toMatch(/M10/);
  expect(value).toContain('2026');
  expect(value).toContain('Asia/Almaty');
});
