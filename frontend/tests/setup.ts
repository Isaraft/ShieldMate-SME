import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

// Node 26 exposes an unavailable global storage getter to jsdom. Model only
// browser preference storage in tests; production still uses window.localStorage.
const preferences = new Map<string, string>();
Object.defineProperty(window, 'localStorage', {
  configurable: true,
  value: {
    get length() {
      return preferences.size;
    },
    clear() {
      preferences.clear();
    },
    getItem(key: string) {
      return preferences.get(key) ?? null;
    },
    setItem(key: string, value: string) {
      preferences.set(key, String(value));
    },
    removeItem(key: string) {
      preferences.delete(key);
    },
    key(index: number) {
      return Array.from(preferences.keys())[index] ?? null;
    },
  } satisfies Storage,
});
