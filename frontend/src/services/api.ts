export class ApiError extends Error {
  status: number;
  error_id: string;
  detail: any;

  constructor(msg: string, status: number, error_id: string, detail: any) {
    super(msg);
    this.name = "ApiError";
    this.status = status;
    this.error_id = error_id;
    this.detail = detail;
  }
}

const API_BASE = "/api/v1";

let authToken: string | null = localStorage.getItem("token");
let refreshToken: string | null = localStorage.getItem("refresh_token");
let refreshPromise: Promise<boolean> | null = null;

export function setToken(token: string | null) {
  authToken = token;
  if (token) localStorage.setItem("token", token);
  else localStorage.removeItem("token");
}

export function setRefreshToken(token: string | null) {
  refreshToken = token;
  if (token) localStorage.setItem("refresh_token", token);
  else localStorage.removeItem("refresh_token");
}

export function getToken(): string | null {
  return authToken;
}

async function tryRefresh(): Promise<boolean> {
  if (!refreshToken) return false;
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      const data = await res.json();
      if (data.success) {
        setToken(data.access_token);
        setRefreshToken(data.refresh_token);
        return true;
      }
      return false;
    } catch {
      return false;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

async function handleResponse(res: Response): Promise<any> {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiError(
      data.error || `HTTP ${res.status}`,
      res.status,
      data.error_id || "",
      data,
    );
  }
  return data;
}

export async function api<T>(method: string, path: string, body?: unknown, _retry = true): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  const res = await fetch(`${API_BASE}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (res.status === 401 && _retry) {
    const refreshed = await tryRefresh();
    if (refreshed) return api<T>(method, path, body, false);
  }
  return handleResponse(res);
}

export async function uploadFile(path: string, file: File, _retry = true): Promise<any> {
  const form = new FormData();
  form.append("file", file);
  const headers: Record<string, string> = {};
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", headers, body: form });
  if (res.status === 401 && _retry) {
    const refreshed = await tryRefresh();
    if (refreshed) return uploadFile(path, file, false);
  }
  return handleResponse(res);
}
