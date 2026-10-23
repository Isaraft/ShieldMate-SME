import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, it, vi } from 'vitest';
import { Assets } from '../src/pages/Assets';
const asset = {
  id: 'asset',
  canonical_fqdn: 'example.com',
  status: 'pending',
  created_at: 1,
  challenge_generation: 1,
  challenge_issued_at: 1,
  challenge_expires_at: 9999999999,
  verified_at: null,
  verification_valid_until: null,
  record_hostname: '_shieldmate-challenge.example.com',
  record_value: 'shieldmate-verification=public-dns-challenge',
};
let rows: (typeof asset)[];
beforeEach(() => {
  rows = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options) => {
      const path = String(url);
      if (path.endsWith('/csrf'))
        return { ok: true, json: async () => ({ csrf_token: 'csrf' }) };
      if (options?.method === 'POST' && path.endsWith('/domains')) {
        rows = [asset];
        return { ok: true, json: async () => asset };
      }
      return { ok: true, json: async () => rows };
    }),
  );
});
function renderAssets() {
  render(
    <MemoryRouter>
      <Assets />
    </MemoryRouter>,
  );
}
it('requires explicit authorization and shows a true empty state', async () => {
  renderAssets();
  expect(
    await screen.findByText('Your domain list starts here.'),
  ).toBeInTheDocument();
  expect(screen.getByRole('checkbox')).not.toBeChecked();
  expect(screen.getByRole('checkbox')).toBeRequired();
});
it('enrolls with consent, displays persisted instructions and disables scans', async () => {
  const user = userEvent.setup();
  renderAssets();
  await screen.findByText('Your domain list starts here.');
  await user.type(
    screen.getByRole('textbox', { name: 'Domain name' }),
    'example.com',
  );
  await user.click(screen.getByRole('checkbox'));
  await user.click(screen.getByRole('button', { name: 'Add domain' }));
  expect(await screen.findByText(asset.record_value)).toBeInTheDocument();
  expect(
    screen.getByRole('button', { name: 'Scan unavailable' }),
  ).toBeDisabled();
  expect(fetch).toHaveBeenCalledWith(
    '/api/v1/domains',
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        fqdn: 'example.com',
        authorization_acknowledged: true,
      }),
    }),
  );
});
it('rejects pasted URLs without silently converting them', async () => {
  const user = userEvent.setup();
  renderAssets();
  await screen.findByText('Your domain list starts here.');
  await user.type(
    screen.getByRole('textbox', { name: 'Domain name' }),
    'https://example.com',
  );
  await user.click(screen.getByRole('checkbox'));
  await user.click(screen.getByRole('button', { name: 'Add domain' }));
  expect(
    await screen.findByText(/Enter a domain only, without whitespace/),
  ).toBeInTheDocument();
  expect(rows).toHaveLength(0);
});
it('shows a recoverable server failure', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: false, status: 503, json: async () => ({}) })),
  );
  renderAssets();
  expect(
    await screen.findByRole('button', { name: 'Retry loading domains' }),
  ).toBeInTheDocument();
});
