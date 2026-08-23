/**
 * Enterprise API Client with JWT Bearer injection and 401 Auto-Refresh Interceptor (platform/src/services/api.ts)
 */

interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

export async function apiClient<T = any>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const url = endpoint.startsWith('/') ? endpoint : `/api/${endpoint}`;
  const accessToken = localStorage.getItem('cornerstone_access_token');

  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (accessToken && !options.skipAuth) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  let response = await fetch(url, { ...options, headers });

  // If 401 Unauthorized, attempt silent token refresh and retry request
  if (response.status === 401 && !options.skipAuth) {
    const refreshToken = localStorage.getItem('cornerstone_refresh_token');
    if (!refreshToken) {
      localStorage.removeItem('cornerstone_access_token');
      localStorage.removeItem('cornerstone_user');
      window.dispatchEvent(new Event('auth:unauthorized'));
      throw new Error('Unauthorized');
    }

    if (!isRefreshing) {
      isRefreshing = true;
      try {
        const refreshRes = await fetch('/api/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (refreshRes.ok) {
          const data = await refreshRes.json();
          const newAccessToken = data.access_token;
          const newRefreshToken = data.refresh_token;
          localStorage.setItem('cornerstone_access_token', newAccessToken);
          if (newRefreshToken) localStorage.setItem('cornerstone_refresh_token', newRefreshToken);
          isRefreshing = false;
          onRefreshed(newAccessToken);
        } else {
          isRefreshing = false;
          localStorage.removeItem('cornerstone_access_token');
          localStorage.removeItem('cornerstone_refresh_token');
          localStorage.removeItem('cornerstone_user');
          window.dispatchEvent(new Event('auth:unauthorized'));
          throw new Error('Session expired');
        }
      } catch (err) {
        isRefreshing = false;
        throw err;
      }
    }

    // Wait for the refreshing process to provide the new token, then retry
    return new Promise((resolve, reject) => {
      addRefreshSubscriber(async (newToken: string) => {
        try {
          headers.set('Authorization', `Bearer ${newToken}`);
          const retryRes = await fetch(url, { ...options, headers });
          if (!retryRes.ok) {
            const errData = await retryRes.json().catch(() => ({}));
            reject(new Error(errData.detail || 'Request failed'));
          } else {
            resolve(await retryRes.json());
          }
        } catch (err) {
          reject(err);
        }
      });
    });
  }

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `HTTP Error ${response.status}`);
  }

  return response.json();
}
