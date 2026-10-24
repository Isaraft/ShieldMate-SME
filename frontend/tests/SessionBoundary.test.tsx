import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { it, expect, vi } from 'vitest';
import { PrivateWorkspace, OrganizationSettings } from '../src/pages/Account';
import { notifySessionChange } from '../src/sessionEvents';
const identity = {
  id: 'a',
  email: 'a@example.com',
  organization: { id: 'org-a', name: 'Tenant A' },
};
function mount() {
  render(
    <MemoryRouter initialEntries={['/app/settings']}>
      <Routes>
        <Route element={<PrivateWorkspace />}>
          <Route path="/app/settings" element={<OrganizationSettings />} />
        </Route>
        <Route path="/login" element={<h1>Signed out</h1>} />
      </Routes>
    </MemoryRouter>,
  );
}
it('hides cached identity during focus verification but preserves same-account drafts', async () => {
  let complete: ((value: unknown) => void) | undefined;
  let calls = 0;
  vi.stubGlobal(
    'fetch',
    vi.fn(() =>
      ++calls === 1
        ? Promise.resolve({ ok: true, json: async () => identity })
        : new Promise((resolve) => {
            complete = resolve;
          }),
    ),
  );
  mount();
  const field = await screen.findByRole('textbox', { name: 'Company name' });
  await userEvent.clear(field);
  await userEvent.type(field, 'Unsaved draft');
  act(() => window.dispatchEvent(new Event('focus')));
  await screen.findByText('Checking your session…');
  expect(screen.getByText('Tenant A')).not.toBeVisible();
  await waitFor(() => expect(complete).toBeDefined());
  await act(async () => complete?.({ ok: true, json: async () => identity }));
  expect(screen.getByRole('textbox', { name: 'Company name' })).toHaveValue(
    'Unsaved draft',
  );
});
it('clears private identity immediately when another tab changes the session', async () => {
  let current = identity;
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, json: async () => current })),
  );
  mount();
  await screen.findByText('Tenant A');
  current = {
    ...identity,
    id: 'b',
    organization: { id: 'org-b', name: 'Tenant B' },
  };
  act(() => notifySessionChange());
  expect(screen.queryByText('Tenant A')).not.toBeInTheDocument();
  await screen.findByText('Tenant B');
  expect(screen.queryByText('Tenant A')).not.toBeInTheDocument();
});
