import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { ServiceStatus } from '../src/components/ServiceStatus';

it('shows loading without claiming a successful connection', () => {
  vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})));
  render(<ServiceStatus />);
  expect(screen.getByRole('status')).toHaveTextContent('Checking connection…');
  expect(screen.queryByText('Responding')).not.toBeInTheDocument();
});

it('reports a connection failure and permits a real retry', async () => {
  const fetchMock = vi
    .fn()
    .mockRejectedValueOnce(new Error('offline'))
    .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'ok' }) });
  vi.stubGlobal('fetch', fetchMock);
  const user = userEvent.setup();
  render(<ServiceStatus />);
  await user.click(
    await screen.findByRole('button', { name: 'Retry connection' }),
  );
  expect(await screen.findByText('Responding')).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledTimes(2);
});

it.each([
  { ok: false, json: async () => ({ status: 'ok' }) },
  { ok: true, json: async () => ({ status: 'unexpected' }) },
])('does not treat an invalid response as success', async (response) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response));
  render(<ServiceStatus />);
  expect(
    await screen.findByText(/Unavailable — start the backend/),
  ).toBeInTheDocument();
});
