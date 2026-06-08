import { api, setToken, setRefreshToken } from "./api";

export type User = {
  id: string;
  username: string;
  email?: string;
  balance: number;
  permissions: string;
  is_admin: boolean;
};

export async function login(username: string, password: string): Promise<User> {
  const res: any = await api("POST", "/auth/login", { username, password });
  if (!res.success) throw new Error(res.error || "Login failed");
  setToken(res.access_token);
  setRefreshToken(res.refresh_token);
  return getMe();
}

export async function getMe(): Promise<User> {
  return api("GET", "/auth/me");
}

export function logout() {
  setToken(null);
  setRefreshToken(null);
}
