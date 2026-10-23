import { useEffect, useState } from 'react';

type Status = 'loading' | 'ready' | 'unavailable';

export function ServiceStatus() {
  const [status, setStatus] = useState<Status>('loading');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const timeout = window.setTimeout(() => controller.abort(), 5000);
    async function check() {
      try {
        const response = await fetch('/api/v1/health', {
          signal: controller.signal,
          headers: { Accept: 'application/json' },
        });
        if (!response.ok) throw new Error('Health endpoint unavailable');
        const body: unknown = await response.json();
        if (
          typeof body !== 'object' ||
          body === null ||
          !('status' in body) ||
          body.status !== 'ok'
        ) {
          throw new Error('Unexpected health response');
        }
        if (active) setStatus('ready');
      } catch {
        if (active) setStatus('unavailable');
      } finally {
        window.clearTimeout(timeout);
      }
    }
    void check();
    return () => {
      active = false;
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [attempt]);

  return (
    <aside className="service-status" aria-label="Local service status">
      <p role="status">
        <span className="eyebrow">Local API</span>
        <span className={`status-value status-${status}`}>
          {status === 'loading' && 'Checking connection…'}
          {status === 'ready' && 'Responding'}
          {status === 'unavailable' &&
            'Unavailable — start the backend, then retry.'}
        </span>
      </p>
      {status === 'unavailable' && (
        <button
          className="text-button"
          onClick={() => {
            setStatus('loading');
            setAttempt((value) => value + 1);
          }}
        >
          Retry connection
        </button>
      )}
      <p className="text-sm">
        Connection status only. No domain checks are running.
      </p>
    </aside>
  );
}
