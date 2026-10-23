import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, ApiError } from '../authApi';

// Key page records by route. Late responses cannot populate another route/session.
export function useWorkspaceResource<T>(path: string, refreshMs = 15000) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const navigate = useNavigate();
  const refresh = useCallback(() => setAttempt((n) => n + 1), []);
  useEffect(() => {
    let active = true;
    let latestRequest = 0;
    async function load() {
      const requestId = ++latestRequest;
      try {
        const value = await api<T>(path);
        if (active && requestId === latestRequest) {
          setData(value);
          setError('');
        }
      } catch (e) {
        if (!active || requestId !== latestRequest) return;
        if (e instanceof ApiError && e.status === 401)
          navigate('/login', { replace: true });
        else
          setError(
            e instanceof Error
              ? e.message
              : 'Unable to load saved data. Retry.',
          );
      }
    }
    void load();
    const focus = () => {
      if (!document.hidden) void load();
    };
    window.addEventListener('focus', focus);
    const interval = refreshMs
      ? window.setInterval(focus, refreshMs)
      : undefined;
    return () => {
      active = false;
      window.removeEventListener('focus', focus);
      window.clearInterval(interval);
    };
  }, [path, attempt, navigate, refreshMs]);
  return { data, error, refresh };
}
