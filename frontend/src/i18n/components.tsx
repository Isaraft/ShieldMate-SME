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
      <button
        type="button"
        lang="en"
        aria-label="English"
        aria-pressed={locale === 'en'}
        onClick={() => setLocale('en')}
      >
        EN
      </button>
      <button
        type="button"
        lang="ru"
        aria-label="Русский"
        aria-pressed={locale === 'ru'}
        onClick={() => setLocale('ru')}
      >
        RU
      </button>
    </fieldset>
  );
}
