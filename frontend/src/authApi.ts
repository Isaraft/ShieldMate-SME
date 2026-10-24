import { notifySessionChange } from './sessionEvents';
export type Organization = {
  id: string;
  name: string;
  created_at: number;
  updated_at: number;
};
export type Identity = {
  id: string;
  email: string;
  organization: Organization | null;
};
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  method = 'GET',
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (method !== 'GET') {
    const response = await fetch('/api/v1/auth/csrf', {
      credentials: 'include',
    });
    if (!response.ok)
      throw new ApiError(
        'Unable to establish a secure request. Retry.',
        response.status,
      );
    const token = (await response.json()) as { csrf_token: string };
    headers['X-CSRF-Token'] = token.csrf_token;
    headers['Content-Type'] = 'application/json';
  }
  const response = await fetch(`/api/v1${path}`, {
    method,
    headers,
    credentials: 'include',
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  if (!response.ok) {
    const data = (await response.json().catch(() => null)) as {
      error?: { message?: string };
    } | null;
    throw new ApiError(
      data?.error?.message ?? 'Request failed. Please retry.',
      response.status,
    );
  }
  if (method === 'POST' && (path === '/auth/login' || path === '/auth/logout'))
    notifySessionChange();
  return response.json() as Promise<T>;
}
