import type { AuthProvider } from "react-admin";
import { apiRequest, setToken } from "./api";

type AuthResult = {
  success: boolean;
  access_token?: string;
  error?: string;
  is_admin?: boolean;
};

export const authProvider: AuthProvider = {
  async login({ username, password }) {
    const result = await apiRequest<AuthResult>("POST", "/auth/login", { username, password });
    if (result.success && result.access_token) {
      if (!result.is_admin) {
        throw new Error("Требуются права администратора");
      }
      setToken(result.access_token);
      localStorage.setItem("token", result.access_token);
      localStorage.setItem("username", username);
    } else {
      throw new Error(result.error || "Login failed");
    }
  },
  async logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    setToken(null);
  },
  async checkError(error) {
    if (error.status === 401 || error.status === 403) {
      localStorage.removeItem("token");
      throw new Error("Session expired");
    }
  },
  async checkAuth() {
    const token = localStorage.getItem("token");
    if (!token) throw new Error("Not authenticated");
    setToken(token);
  },
  async getPermissions() {
    const token = localStorage.getItem("token");
    if (!token) return undefined;
    setToken(token);
    try {
      const result = await apiRequest<AuthResult>("GET", "/auth/me");
      return result.is_admin ? "admin" : "user";
    } catch {
      return undefined;
    }
  },
  async getIdentity() {
    const username = localStorage.getItem("username") || "admin";
    return { id: username, fullName: username };
  },
};
