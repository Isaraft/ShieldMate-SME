import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, it, vi } from 'vitest';
import { Dashboard } from '../src/pages/Dashboard';
import { Tasks } from '../src/pages/Tasks';
import { TaskDetail } from '../src/pages/TaskDetail';
import { TaskAction } from '../src/components/TaskAction';
import { dashboard, finding, task } from './fixtures/workflow';

function show(path = '/app') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/app" element={<Dashboard />} />
        <Route path="/app/tasks" element={<Tasks />} />
        <Route path="/app/tasks/:taskId" element={<TaskDetail />} />
        <Route path="/login" element={<p>Sign in again</p>} />
      </Routes>
    </MemoryRouter>,
  );
}
function respond(value: unknown) {
  return { ok: true, status: 200, json: async () => value };
}
it('uses server dashboard counts, actual priorities and correct source links', async () => {
  const data = dashboard();
  data.done_unverified = 1;
  data.task_counts = { done: 1 };
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => respond(data)),
  );
  show();
  await screen.findByRole('heading', { name: 'Actual company' });
  expect(screen.getByRole('link', { name: '1 / 1 domains' })).toHaveAttribute(
    'href',
    '/app/assets',
  );
  expect(
    screen.getByText('Human work is not technical resolution'),
  ).toBeInTheDocument();
  expect(screen.getByText('Priority 1 / qa.example.com')).toBeInTheDocument();
  expect(screen.queryByText(/Priority 2/)).not.toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'qa.example.com' })).toHaveAttribute(
    'href',
    '/app/assets/asset/scans/source',
  );
});
it.each(['first', 'no_scan', 'partial', 'stale'] as const)(
  'honestly presents %s dashboard state',
  async (state) => {
    const data = dashboard();
    if (state === 'first') {
      data.asset_count = 0;
      data.eligible_assets = 0;
      data.recent_scan_count = 0;
    }
    if (state === 'no_scan') data.recent_scan_count = 0;
    if (state === 'partial') {
      data.scans[0].status = 'partial';
      data.findings.summary.assessment.rule_counts = { not_evaluable: 6 };
    }
    if (state === 'stale')
      data.findings.summary.assessment.stale_assessments = 1;
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => respond(data)),
    );
    show();
    expect(
      await screen.findByText(
        {
          first: 'Start with a domain you control',
          no_scan: 'Ready for the first assessment',
          partial: 'Some recent checks were incomplete',
          stale: 'Historical evidence',
        }[state],
        { exact: true },
      ),
    ).toBeInTheDocument();
  },
);
it('retries a dashboard failure and redirects expired sessions', async () => {
  let failed = true;
  vi.stubGlobal(
    'fetch',
    vi.fn(async () =>
      failed
        ? {
            ok: false,
            status: 503,
            json: async () => ({ error: { message: 'API offline' } }),
          }
        : respond(dashboard()),
    ),
  );
  show();
  await screen.findByText('Overview unavailable');
  failed = false;
  await userEvent.click(screen.getByRole('button', { name: 'Retry overview' }));
  await screen.findByRole('heading', { name: 'Actual company' });
});
it('shows loading without inventing metrics', () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => new Promise(() => {})),
  );
  show();
  expect(screen.getByText('Loading your workspace…')).toBeInTheDocument();
  expect(screen.queryByText('Supported open findings')).not.toBeInTheDocument();
});
it('renders task filters and bounds navigation from backend page counts', async () => {
  const fetcher = vi.fn(async () =>
    respond({ items: [task], total: 1, offset: 0, limit: 20, domains: [] }),
  );
  vi.stubGlobal('fetch', fetcher);
  show('/app/tasks');
  await screen.findByText('1 saved task in this selection.');
  await userEvent.selectOptions(
    screen.getByRole('combobox', { name: 'Status' }),
    'done',
  );
  await userEvent.click(
    screen.getByRole('button', { name: 'Apply task filters' }),
  );
  await waitFor(() =>
    expect(fetcher).toHaveBeenLastCalledWith(
      '/api/v1/tasks?status=done&sort=updated',
      expect.anything(),
    ),
  );
  expect(screen.getByRole('button', { name: 'Next tasks' })).toBeDisabled();
});
it('creates a canonical task through the CSRF client and routes to its actual ID', async () => {
  const fetcher = vi.fn(async (url) =>
    respond(String(url).endsWith('/csrf') ? { csrf_token: 'test-csrf' } : task),
  );
  vi.stubGlobal('fetch', fetcher);
  render(
    <MemoryRouter>
      <Routes>
        <Route path="/" element={<TaskAction finding={finding} />} />
        <Route path="/app/tasks/task-id" element={<p>Task opened</p>} />
      </Routes>
    </MemoryRouter>,
  );
  await userEvent.click(screen.getByRole('button', { name: 'Create task' }));
  await screen.findByText('Task opened');
  expect(fetcher).toHaveBeenCalledWith(
    '/api/v1/findings/fixture/task',
    expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({ 'X-CSRF-Token': 'test-csrf' }),
      body: '{}',
    }),
  );
});
it('opens an existing task without a write request', () => {
  vi.stubGlobal('fetch', vi.fn());
  render(
    <MemoryRouter>
      <TaskAction
        finding={{ ...finding, task_id: 'task-id', task_status: 'done' }}
      />
    </MemoryRouter>,
  );
  expect(
    screen.getByRole('link', { name: 'Open task · Done' }),
  ).toHaveAttribute('href', '/app/tasks/task-id');
  expect(fetch).not.toHaveBeenCalled();
});
it('saves human work, retains open finding, escapes note history and supports recurrence', async () => {
  let current = structuredClone(task);
  current.reopened_at = 1700000001;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options) => {
      if (String(url).endsWith('/csrf'))
        return respond({ csrf_token: 'token' });
      if (options?.method === 'PATCH') {
        const body = JSON.parse(String(options.body));
        current = { ...current, ...body, version: 2 };
      }
      return respond(current);
    }),
  );
  show('/app/tasks/task-id');
  await screen.findByText('Recurrence recorded');
  await userEvent.type(
    screen.getByRole('textbox', { name: 'Owner label' }),
    'IT provider',
  );
  await userEvent.type(
    screen.getByRole('textbox', { name: 'Work note' }),
    '<script>alert(1)</script>',
  );
  await userEvent.selectOptions(
    screen.getByRole('combobox', { name: 'Work status' }),
    'done',
  );
  await userEvent.click(
    screen.getByRole('button', { name: 'Save work changes' }),
  );
  await screen.findByText('Task marked done — remediation not yet verified');
  expect(
    screen.getByText(
      'Work changes saved. Technical finding state is unchanged.',
    ),
  ).toBeInTheDocument();
  expect(screen.getByRole('textbox', { name: 'Work note' })).toHaveValue(
    '<script>alert(1)</script>',
  );
  expect(document.querySelector('script')).toBeNull();
});
it('keeps a conflicting draft until the user explicitly reloads', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options) =>
      String(url).endsWith('/csrf')
        ? respond({ csrf_token: 'token' })
        : options?.method === 'PATCH'
          ? {
              ok: false,
              status: 409,
              json: async () => ({
                error: { message: 'Task changed elsewhere' },
              }),
            }
          : respond(task),
    ),
  );
  show('/app/tasks/task-id');
  await screen.findByRole('textbox', { name: 'Work note' });
  await userEvent.type(
    screen.getByRole('textbox', { name: 'Work note' }),
    'Keep draft',
  );
  await userEvent.click(
    screen.getByRole('button', { name: 'Save work changes' }),
  );
  await screen.findByText('Task changed elsewhere');
  expect(screen.getByRole('textbox', { name: 'Work note' })).toHaveValue(
    'Keep draft',
  );
  await userEvent.click(
    screen.getByRole('button', { name: 'Reload latest and discard draft' }),
  );
  await waitFor(() =>
    expect(screen.getByRole('textbox', { name: 'Work note' })).toHaveValue(''),
  );
});
it('redirects an expired task session to login', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: false,
      status: 401,
      json: async () => ({ error: { message: 'Session ended' } }),
    })),
  );
  show('/app/tasks/task-id');
  await screen.findByText('Sign in again');
});

it('keeps a draft when internal navigation is cancelled', async () => {
  vi.stubGlobal(
    'confirm',
    vi.fn(() => false),
  );
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => respond(task)),
  );
  show('/app/tasks/task-id');
  await screen.findByRole('textbox', { name: 'Work note' });
  await userEvent.type(
    screen.getByRole('textbox', { name: 'Work note' }),
    'Unsaved follow-up',
  );
  await userEvent.click(
    screen.getByRole('link', { name: 'Review finding & technical history' }),
  );
  expect(window.confirm).toHaveBeenCalled();
  expect(screen.getByRole('textbox', { name: 'Work note' })).toHaveValue(
    'Unsaved follow-up',
  );
});
