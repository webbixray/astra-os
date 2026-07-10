const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const REQUEST_TIMEOUT = 30000;
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 500;

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

interface Envelope<T> {
  success: boolean;
  data?: T;
  code?: string;
  message?: string;
}

function getCsrfToken(): string | null {
  if (typeof window === 'undefined') return null;
  const match = document.cookie.match(/(?:^|;\s*)astra_csrf=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

function getStoredTokens() {
  if (typeof window === 'undefined') return { accessToken: null, refreshToken: null };
  return {
    accessToken: localStorage.getItem('astra_access_token'),
    refreshToken: localStorage.getItem('astra_refresh_token'),
  };
}

function clearAuth() {
  localStorage.removeItem('astra_access_token');
  localStorage.removeItem('astra_refresh_token');
  localStorage.removeItem('astra_user');
  localStorage.removeItem('astra_orgs');
}

async function attemptTokenRefresh(): Promise<boolean> {
  const { refreshToken } = getStoredTokens();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
      credentials: 'include',
    });

    if (!response.ok) return false;

    const envelope: Envelope<{ access_token: string; refresh_token: string }> = await response.json();
    if (!envelope.success || !envelope.data) return false;

    localStorage.setItem('astra_access_token', envelope.data.access_token);
    localStorage.setItem('astra_refresh_token', envelope.data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

function shouldRetry(status: number): boolean {
  return (
    status === 429 ||
    status === 502 ||
    status === 503 ||
    status === 504 ||
    status === 0
  );
}

async function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  get isAuthError(): boolean {
    return this.status === 401;
  }

  get isRateLimited(): boolean {
    return this.status === 429;
  }

  get isServerError(): boolean {
    return this.status >= 500;
  }
}

async function request<T>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    headers?: Record<string, string>;
    timeout?: number;
    skipAuth?: boolean;
    signal?: AbortSignal;
  } = {},
): Promise<T> {
  const {
    method = 'GET',
    body,
    headers = {},
    timeout = REQUEST_TIMEOUT,
    skipAuth = false,
    signal,
  } = options;

  const { accessToken } = getStoredTokens();
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  const combinedSignal = signal
    ? combineAbortSignals(controller.signal, signal)
    : controller.signal;

  const makeRequest = async (
    token: string | null,
    attempt: number,
  ): Promise<Response> => {
    const csrfToken = getCsrfToken();
    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    if (token && !skipAuth) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }

    if (csrfToken && method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
      requestHeaders['X-CSRF-Token'] = csrfToken;
    }

    return fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
      signal: combinedSignal,
      credentials: 'include',
    });
  };

  const executeWithRetry = async (attempt: number): Promise<T> => {
    try {
      let response = await makeRequest(accessToken, attempt);

      if (response.status === 401 && !skipAuth) {
        if (!isRefreshing) {
          isRefreshing = true;
          refreshPromise = attemptTokenRefresh().finally(() => {
            isRefreshing = false;
            refreshPromise = null;
          });
        }

        const refreshed = await refreshPromise;
        if (refreshed) {
          const { accessToken: newToken } = getStoredTokens();
          response = await makeRequest(newToken, attempt);
        } else {
          clearAuth();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
          throw new ApiError(401, 'session_expired', 'Session expired. Please log in again.');
        }
      }

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        const apiError = new ApiError(
          response.status,
          errorBody.code || 'http_error',
          errorBody.message || errorBody.detail || `HTTP ${response.status}`,
          errorBody.errors || errorBody.details,
        );

        if (shouldRetry(response.status) && attempt < MAX_RETRIES - 1) {
          const backoffDelay = RETRY_DELAY_MS * Math.pow(2, attempt) * (0.5 + Math.random() * 0.5);
          await delay(backoffDelay);
          return executeWithRetry(attempt + 1);
        }

        throw apiError;
      }

      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const envelope: Envelope<T> = await response.json();
        if (!envelope.success) {
          throw new ApiError(
            response.status,
            envelope.code || 'request_failed',
            envelope.message || 'Request failed',
          );
        }
        return envelope.data as T;
      }
      return response.text() as unknown as T;
    } catch (err) {
      if (err instanceof ApiError) throw err;
      if (err instanceof DOMException && err.name === 'AbortError') {
        throw new ApiError(0, 'timeout', 'Request timed out');
      }

      if (attempt < MAX_RETRIES - 1) {
        const backoffDelay = RETRY_DELAY_MS * Math.pow(2, attempt) * (0.5 + Math.random() * 0.5);
        await delay(backoffDelay);
        return executeWithRetry(attempt + 1);
      }

      throw new ApiError(
        0,
        'network_error',
        err instanceof Error ? err.message : 'Network request failed',
      );
    }
  };

  try {
    return await executeWithRetry(0);
  } finally {
    clearTimeout(timeoutId);
  }
}

function combineAbortSignals(...signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();
  const onAbort = () => controller.abort();
  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort();
      return controller.signal;
    }
    signal.addEventListener('abort', onAbort, { once: true });
  }
  return controller.signal;
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) =>
    request<T>(path, { signal }),
  post: <T>(path: string, body?: unknown, skipAuth?: boolean, signal?: AbortSignal) =>
    request<T>(path, { method: 'POST', body, skipAuth, signal }),
  put: <T>(path: string, body: unknown, signal?: AbortSignal) =>
    request<T>(path, { method: 'PUT', body, signal }),
  patch: <T>(path: string, body: unknown, signal?: AbortSignal) =>
    request<T>(path, { method: 'PATCH', body, signal }),
  delete: <T>(path: string, signal?: AbortSignal) =>
    request<T>(path, { method: 'DELETE', signal }),
};

export { ApiError };
