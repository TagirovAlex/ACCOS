const API_BASE = "/api/v1";

let authToken: string | null = null;

export function setToken(token: string | null) {
  authToken = token;
}

export function getToken(): string | null {
  return authToken;
}

export async function apiRequest<T>(
  method: string,
  path: string,
  body?: unknown
): Promise<T> {
  const headers: Record<string, string> = {};
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { ...headers, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    let errorBody = await response.text();
    try {
      const json = JSON.parse(errorBody);
      errorBody = json.detail || json.error || json.message || errorBody;
    } catch {}
    errorBody = errorBody.replace(/<[^>]+>/g, '').trim();
    throw new Error(errorBody || `HTTP ${response.status}`);
  }
  return response.json();
}
