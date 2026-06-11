import type { AuthProvider } from "react-admin";
import { apiRequest, setToken } from "./api";

type AuthResult = {
  success: boolean;
  access_token?: string;
  error?: string;
  is_admin?: boolean;
  admin_role?: string;
  permissions?: string;
};

function getAdminToken(): string | null {
  return localStorage.getItem("admin_token") || localStorage.getItem("token") || null;
}

function setAdminToken(token: string) {
  localStorage.setItem("admin_token", token);
  localStorage.removeItem("token");
}

function removeAdminToken() {
  localStorage.removeItem("admin_token");
  localStorage.removeItem("token");
  localStorage.removeItem("user_permissions");
}

export const authProvider: AuthProvider = {
  async login({ username, password }) {
    const result = await apiRequest<AuthResult>("POST", "/auth/login", { username, password });
    if (result.success && result.access_token) {
      const role = result.admin_role === "super_admin" ? "super_admin" : result.is_admin ? "admin" : "none";
      const perms = (result.permissions || "chat").split(",").filter(Boolean);
      const hasNonChatPerms = perms.some(p => p !== "chat");
      if (role === "none" && !hasNonChatPerms) {
        throw new Error("Требуются права администратора");
      }
      setToken(result.access_token);
      setAdminToken(result.access_token);
      localStorage.setItem("username", username);
      localStorage.setItem("admin_role", role);
      localStorage.setItem("user_permissions", result.permissions || "chat");
    } else {
      throw new Error(result.error || "Login failed");
    }
  },
  async logout() {
    removeAdminToken();
    localStorage.removeItem("username");
    setToken(null);
  },
  async checkError(error) {
    if (error.status === 401) {
      removeAdminToken();
      throw new Error("Session expired");
    }
  },
  async checkAuth() {
    const token = getAdminToken();
    if (!token) throw new Error("Not authenticated");
    setToken(token);
    if (localStorage.getItem("token") && !localStorage.getItem("admin_token")) {
      setAdminToken(token);
    }
  },
    async getPermissions() {
    const token = getAdminToken();
    if (!token) return undefined;
    setToken(token);
    try {
      const result = await apiRequest<AuthResult>("GET", "/auth/me");
      const role = result.admin_role === "super_admin" ? "super_admin" : result.is_admin ? "admin" : "none";
      const perms_str = result.permissions || "chat";
      const perms = perms_str.split(",").filter(Boolean);
      const hasNonChatPerms = perms.some(p => p !== "chat");
      const effectiveRole = role === "super_admin" ? "super_admin" : role === "admin" ? "admin" : (hasNonChatPerms ? perms_str : "none");
      localStorage.setItem("admin_role", role);
      localStorage.setItem("user_permissions", perms_str);
      return effectiveRole;
    } catch {
      return undefined;
    }
  },
  async getIdentity() {
    const username = localStorage.getItem("username") || "admin";
    return { id: username, fullName: username };
  },
};
