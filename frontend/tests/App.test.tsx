import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/App';

function renderRoute(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.stubGlobal('scrollTo', vi.fn());
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ status: 'ok' }) }),
  );
});

describe('public site and preserved foundation routes', () => {
  it('renders the landing page without making product API requests', () => {
    renderRoute();
    expect(
      screen.getByRole('heading', { name: /know what to fix first/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Create workspace' }),
    ).toBeDisabled();
    expect(fetch).not.toHaveBeenCalled();
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    expect(screen.getByText('Planned Starter workflow')).toBeInTheDocument();
  });

  it('supports navigation and moves focus to the new content', async () => {
    const user = userEvent.setup();
    renderRoute('/app');
    const nav = screen.getByRole('navigation', {
      name: 'Workspace navigation',
    });
    await user.click(within(nav).getByRole('link', { name: /assets/i }));
    expect(screen.getByRole('heading', { name: 'Assets' })).toBeInTheDocument();
    expect(screen.getByRole('main')).toHaveFocus();
    expect(within(nav).getByRole('link', { name: /assets/i })).toHaveAttribute(
      'aria-current',
      'page',
    );
  });

  it.each([
    ['/app', 'Overview'],
    ['/app/assets', 'Assets'],
    ['/app/findings', 'Findings'],
    ['/app/tasks', 'Action plan'],
    ['/app/reports', 'Reports'],
    ['/login', 'Sign in'],
    ['/register', 'Create workspace'],
    ['/demo', 'Sample Demo'],
  ])('labels %s as a future feature', (path, title) => {
    renderRoute(path);
    expect(screen.getByRole('heading', { name: title })).toBeInTheDocument();
    expect(screen.getByText('Coming in a later phase')).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('provides a 404 and a working return link', async () => {
    const user = userEvent.setup();
    renderRoute('/unknown');
    expect(
      screen.getByRole('heading', { name: 'This path ends here.' }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole('link', { name: 'Return to home' }));
    expect(
      screen.getByRole('heading', { name: /know what to fix first/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole('main')).toHaveFocus();
  });
});
