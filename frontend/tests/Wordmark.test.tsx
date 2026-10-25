import { act, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, it } from 'vitest';
import { Wordmark } from '../src/components/SiteChrome';
import { setLocale, type Locale } from '../src/i18n';

afterEach(() => act(() => setLocale('en')));

it.each(['en', 'ru', 'kk'] as Locale[])(
  'includes the visible brand words in the accessible name in %s',
  (locale) => {
    setLocale(locale);
    render(
      <MemoryRouter>
        <Wordmark />
      </MemoryRouter>,
    );
    const link = screen.getByRole('link');
    const visible = link.cloneNode(true) as HTMLElement;
    visible
      .querySelectorAll('[aria-hidden="true"]')
      .forEach((node) => node.remove());
    const visibleText = visible.textContent
      ?.replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
    expect(visibleText).toBeTruthy();
    expect(link.getAttribute('aria-label')?.toLowerCase()).toContain(
      visibleText,
    );
  },
);
