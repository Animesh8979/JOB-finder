import toast from 'react-hot-toast';

interface FetchOptions extends RequestInit {
  showToastOnError?: boolean;
}

/** Pull a cookie value by name (handles the documented `name=value; name2=value2` shape). */
export function getCookie(name: string): string | undefined {
  if (typeof document === 'undefined') return undefined;
  const target = `${name}=`;
  for (const part of document.cookie.split(';')) {
    const trimmed = part.trim();
    if (trimmed.startsWith(target)) {
      return decodeURIComponent(trimmed.slice(target.length));
    }
  }
  return undefined;
}

export const apiFetch = async (url: string, options: FetchOptions = {}): Promise<Response> => {
  const { showToastOnError = true, ...fetchOptions } = options;

  // Make sure we always include credentials so any csrftoken cookie round-trips.
  fetchOptions.credentials = fetchOptions.credentials ?? 'same-origin';

  // For state-mutating methods, echo the csrftoken cookie as a header IF the
  // backend has been configured to issue one. The cookie is set by the first
  // GET response automatically. Older backend builds may not set it — in that
  // case the header is omitted and the request still succeeds locally.
  const method = (fetchOptions.method ?? 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
    const token = getCookie('csrftoken');
    if (token) {
      fetchOptions.headers = {
        ...(fetchOptions.headers ?? {}),
        'X-CSRF-Token': token,
      };
    }
  }

  try {
    const response = await fetch(url, fetchOptions);

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        // Read the body EXACTLY once (a failed .json() leaves the stream
        // consumed; calling .text() afterwards throws "body stream already
        // read", which used to surface as a bogus "Network Error" toast).
        const raw = await response.text();
        try {
          const errorData = JSON.parse(raw);
          if (errorData?.detail) {
            errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
          }
        } catch {
          if (raw) errorMessage = raw.substring(0, 100);
        }
      } catch {
        // Body unreadable (network-level failure) — keep the status-code message.
      }

      if (showToastOnError) {
        toast.error(`API Error: ${errorMessage}`);
      }
      throw new Error(errorMessage);
    }

    return response;
  } catch (error) {
    if (showToastOnError && error instanceof Error && !error.message.startsWith('API Error')) {
      toast.error(`Network Error: ${error instanceof Error ? error.message : String(error)}`);
    }
    throw error;
  }
};
