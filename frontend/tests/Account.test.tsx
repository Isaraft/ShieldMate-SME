import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, it, vi } from 'vitest';
import { App } from '../src/App';
function route(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}
beforeEach(() => {
  vi.stubGlobal('scrollTo', vi.fn());
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url) => ({
      ok: String(url).endsWith('/csrf'),
      status: 401,
      json: async () =>
        String(url).endsWith('/csrf')
          ? { csrf_token: 'test-token' }
          : { error: { message: 'Sign in to continue' } },
    })),
  );
});
it.each([
  '/app',
  '/app/settings',
  '/app/assets',
  '/app/findings',
  '/app/tasks',
  '/app/reports',
])('guards %s using the real me contract', async (path) => {
  route(path);
  expect(
    await screen.findByRole('heading', { name: 'Sign in' }),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole('heading', { name: 'Overview' }),
  ).not.toBeInTheDocument();
});
it('shows a loading state without private content while checking identity', () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => new Promise(() => {})),
  );
  route('/app');
  expect(screen.getByText('Checking your session…')).toBeInTheDocument();
  expect(screen.queryByText('Organization settings')).not.toBeInTheDocument();
});
it('renders real company and account identity', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        id: 'user-id',
        email: 'owner@example.com',
        organization: { id: 'org', name: 'Actual company' },
      }),
    })),
  );
  route('/app');
  expect(
    await screen.findByRole('heading', { name: 'Actual company' }),
  ).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Sign out' })).toBeInTheDocument();
});
it('directs an account without a company to onboarding', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        id: 'user-id',
        email: 'owner@example.com',
        organization: null,
      }),
    })),
  );
  route('/app');
  expect(
    await screen.findByRole('heading', { name: 'Create your workspace' }),
  ).toBeInTheDocument();
  expect(screen.getByRole('textbox', { name: 'Company name' })).toBeRequired();
});
it('submits credentials using a CSRF header and HttpOnly-cookie transport', async () => {
  const user = userEvent.setup();
  route('/login');
  await user.type(
    screen.getByRole('textbox', { name: 'Email address' }),
    'owner@example.com',
  );
  await user.type(screen.getByLabelText('Password'), 'a long test passphrase');
  await user.click(screen.getByRole('button', { name: 'Sign in' }));
  expect(await screen.findByText('Unable to continue')).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledWith(
    '/api/v1/auth/login',
    expect.objectContaining({
      credentials: 'include',
      method: 'POST',
      headers: expect.objectContaining({ 'X-CSRF-Token': 'test-token' }),
    }),
  );
});
it('registration exposes usable labels and password boundaries', () => {
  route('/register');
  expect(
    screen.getByRole('heading', { name: 'Create account' }),
  ).toBeInTheDocument();
  expect(screen.getByLabelText('Password')).toHaveAttribute('minlength', '12');
  expect(screen.getByLabelText('Password')).toHaveAttribute(
    'autocomplete',
    'new-password',
  );
});

it('registration waits for completion and shows failures without navigation', async () => {
  const user = userEvent.setup();
  route('/register');
  await user.type(
    screen.getByRole('textbox', { name: 'Email address' }),
    'owner@example.com',
  );
  await user.type(screen.getByLabelText('Password'), 'a long test passphrase');
  await user.click(screen.getByRole('button', { name: 'Create account' }));
  expect(await screen.findByText('Unable to continue')).toBeInTheDocument();
  expect(
    screen.getByRole('heading', { name: 'Create account' }),
  ).toBeInTheDocument();
});
