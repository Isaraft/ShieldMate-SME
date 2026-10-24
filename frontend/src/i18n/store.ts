import { useSyncExternalStore } from 'react';
import english from '../../../backend/app/locales/en.json';
import russian from '../../../backend/app/locales/ru.json';
import kazakh from '../../../backend/app/locales/kk.json';
export type Locale = 'en' | 'ru' | 'kk';
export type MessageKey = keyof typeof english;
const listeners = new Set<() => void>();
let language: Locale = 'en';
try {
  const saved = window.localStorage.getItem('shieldmate-language');
  const browser = navigator.language.split('-')[0];
  language =
    saved === 'ru' || saved === 'kk' || saved === 'en'
      ? saved
      : saved
        ? 'en'
        : browser === 'ru' || browser === 'kk'
          ? browser
          : 'en';
} catch {
  /* Storage may be disabled; memory preference still works. */
}
document.documentElement.lang = language;
export function getLocale(): Locale {
  return language;
}
export function localeName() {
  return { en: 'en-GB', ru: 'ru-KZ', kk: 'kk-KZ' }[language];
}
export function setLocale(next: Locale) {
  language = next === 'ru' || next === 'kk' ? next : 'en';
  document.documentElement.lang = language;
  try {
    window.localStorage.setItem('shieldmate-language', language);
  } catch {
    /* No security data is stored. */
  }
  listeners.forEach((update) => update());
}
export function useLocale() {
  return useSyncExternalStore(
    (update) => {
      listeners.add(update);
      return () => {
        listeners.delete(update);
      };
    },
    getLocale,
    () => 'en' as Locale,
  );
}
export function tr(value: string, locale: Locale = language): string {
  const key = value.replace(/\s+/g, ' ').trim();
  const catalog = { en: english, ru: russian, kk: kazakh }[locale];
  const translated = (catalog as Record<string, string>)[key];
  if (!translated) {
    const match =
      /^(High|Medium|Low|Info) severity; urgency ([0-3])\/3; observed relevance ([0-2])\/2; (conclusive|contextual) evidence\. Ties use newest issue observation, then stable fingerprint\. These are ordering labels, not a risk score\.$/.exec(
        value,
      );
    if (!match) return value;
    const template =
      '{severity} severity; urgency {urgency}/3; observed relevance {relevance}/2; {confidence} evidence. Ties use newest issue observation, then stable fingerprint. These are ordering labels, not a risk score.';
    return tr(template, locale)
      .replace('{severity}', tr(match[1].toLowerCase(), locale))
      .replace('{urgency}', match[2])
      .replace('{relevance}', match[3])
      .replace('{confidence}', tr(match[4], locale));
  }
  return (
    (value.startsWith(' ') ? ' ' : '') +
    translated +
    (value.endsWith(' ') ? ' ' : '')
  );
}
export function t(key: MessageKey, locale: Locale = language) {
  return tr(key, locale);
}

export function dateTime(value: number | null) {
  return value === null
    ? tr('Not yet')
    : new Intl.DateTimeFormat(localeName(), {
        year: 'numeric',
        month: language === 'kk' ? '2-digit' : 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Almaty',
        timeZoneName: 'shortOffset',
      }).format(value * 1000) + ' (Asia/Almaty)';
}

export function format(
  key: MessageKey,
  values: Record<string, string | number>,
): string {
  return tr(key).replace(/\{([a-zA-Z_]+)\}/g, (_, name: string) =>
    typeof values[name] === 'number'
      ? number(values[name] as number)
      : String(values[name] ?? `{${name}}`),
  );
}
export function number(value: number): string {
  return new Intl.NumberFormat(localeName()).format(value);
}
