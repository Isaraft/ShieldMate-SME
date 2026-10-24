import type { ReactNode } from 'react';
import { useLocale, tr, setLocale } from './store';
export function T({ children, text }: { children?: ReactNode; text?: string }) {
  const locale = useLocale();
  const value = text ?? children;
  return typeof value === 'string' ? tr(value, locale) : value;
}
export function LanguageSwitch() {
  const locale = useLocale();
  return (
    <fieldset className="language-switch">
      <legend className="sr-only">{tr('Language')}</legend>
      {(
        [
          ['en', 'English'],
          ['ru', 'Русский'],
          ['kk', 'Қазақша'],
        ] as const
      ).map(([code, name]) => (
        <button
          key={code}
          type="button"
          lang={code}
          aria-label={name}
          aria-pressed={locale === code}
          onClick={() => setLocale(code)}
        >
          {name}
        </button>
      ))}
    </fieldset>
  );
}
