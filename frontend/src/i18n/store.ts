import { useSyncExternalStore } from 'react';
import russian from '../../../backend/app/locales/ru.json';
export type Locale = 'en' | 'ru';
export type MessageKey = keyof typeof russian;
const listeners = new Set<() => void>();
let language: Locale = 'en';
try {
  const saved = window.localStorage.getItem('shieldmate-language');
  language =
    saved === 'ru' || (!saved && navigator.language.startsWith('ru'))
      ? 'ru'
      : 'en';
} catch {
  /* Storage may be disabled; memory preference still works. */
}
document.documentElement.lang = language;
export function getLocale(): Locale {
  return language;
}
export function localeName() {
  return language === 'ru' ? 'ru-RU' : 'en-GB';
}
export function setLocale(next: Locale) {
  language = next === 'ru' ? 'ru' : 'en';
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
  if (locale === 'en') return value;
  const key = value.replace(/\s+/g, ' ').trim();
  const translated = (russian as Record<string, string>)[key];
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
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Almaty',
        timeZoneName: 'shortOffset',
      }).format(value * 1000) + ' (Asia/Almaty)';
}
