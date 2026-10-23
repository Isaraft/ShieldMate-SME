import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, it, vi } from 'vitest';
import { App } from '../src/App';
import { Button, Field } from '../src/components/ui/Primitives';

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

it('links every public section to a real focusable destination', async () => {
  const user = userEvent.setup();
  renderRoute();
  for (const [label, id] of [
    ['Product', 'product'],
    ['How it works', 'how-it-works'],
    ['Who it’s for', 'who-its-for'],
    ['Scope', 'scope'],
  ]) {
    await user.click(screen.getByRole('button', { name: 'Menu' }));
    const nav = screen.getByRole('navigation', { name: 'Main navigation' });
    await user.click(within(nav).getByRole('link', { name: label }));
    expect(document.getElementById(id)).toHaveFocus();
    expect(screen.getByRole('button', { name: 'Menu' })).toHaveAttribute(
      'aria-expanded',
      'false',
    );
  }
  await user.click(screen.getByRole('link', { name: 'See how it works' }));
  expect(document.getElementById('how-it-works')).toHaveFocus();
});

it('dismisses the navigation with Escape and restores toggle focus', async () => {
  const user = userEvent.setup();
  renderRoute();
  await user.click(screen.getByRole('button', { name: 'Menu' }));
  expect(screen.getByRole('button', { name: 'Close menu' })).toHaveAttribute(
    'aria-expanded',
    'true',
  );
  await user.tab();
  await user.keyboard('{Escape}');
  expect(screen.getByRole('button', { name: 'Menu' })).toHaveFocus();
  expect(screen.getByRole('button', { name: 'Menu' })).toHaveAttribute(
    'aria-expanded',
    'false',
  );
});

it('routes the preview CTA to an honest workspace and only requests health', async () => {
  const user = userEvent.setup();
  renderRoute();
  await user.click(
    screen.getByRole('link', { name: 'View interface preview' }),
  );
  expect(
    screen.getByText(
      'Live features are under development. No account or workspace data.',
    ),
  ).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Run a check' })).toBeDisabled();
  expect(await screen.findByText('Responding')).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledWith('/api/v1/health', expect.any(Object));
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
});

it('shows an empty findings table without fabricated results', () => {
  renderRoute('/app/findings');
  const table = screen.getByRole('table', {
    name: 'Findings structure — no results available',
  });
  expect(within(table).getAllByRole('row')).toHaveLength(2);
  expect(
    within(table).getByText(/An empty table is not evidence/),
  ).toBeInTheDocument();
});

it('validates the component example, restores input focus, resets, and never sends data', async () => {
  const user = userEvent.setup();
  renderRoute('/app/ui-kit');
  const input = screen.getByRole('textbox', { name: 'Example label' });
  await user.click(screen.getByRole('button', { name: 'Try validation' }));
  expect(input).toHaveFocus();
  expect(input).toHaveAttribute('aria-invalid', 'true');
  expect(input).toHaveAccessibleDescription(/Enter at least 3 characters/);
  await user.type(input, 'Example');
  await user.click(screen.getByRole('button', { name: 'Try validation' }));
  expect(screen.getByText('Example validated')).toBeInTheDocument();
  expect(input).toHaveAttribute('aria-invalid', 'false');
  await user.click(screen.getByRole('button', { name: 'Reset' }));
  expect(input).toHaveValue('');
  expect(screen.queryByText('Example validated')).not.toBeInTheDocument();
  expect(fetch).not.toHaveBeenCalled();
});

it('keeps disabled and pending controls inert and out of tab order', async () => {
  const click = vi.fn();
  const user = userEvent.setup();
  render(
    <>
      <Button disabled onClick={click}>
        Unavailable
      </Button>
      <Button pending onClick={click}>
        Submit
      </Button>
      <Button>Available</Button>
    </>,
  );
  await user.click(screen.getByRole('button', { name: 'Unavailable' }));
  const pending = screen.getByRole('button', { name: 'Please wait…' });
  expect(pending).toHaveAttribute('aria-busy', 'true');
  expect(pending).toBeDisabled();
  await user.tab();
  expect(screen.getByRole('button', { name: 'Available' })).toHaveFocus();
  expect(click).not.toHaveBeenCalled();
});

it('associates field labels, help and errors with a unique input', () => {
  render(
    <>
      <Field label="First example" help="Example help" error="Example error" />
      <Field label="Second example" help="Another help" />
    </>,
  );
  const input = screen.getByRole('textbox', { name: 'First example' });
  expect(input).toHaveAccessibleDescription(
    'Example help Error: Example error',
  );
  expect(input.id).not.toEqual(
    screen.getByRole('textbox', { name: 'Second example' }).id,
  );
});
