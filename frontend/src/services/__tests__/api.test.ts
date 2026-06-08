import { describe, it, expect, vi, beforeEach } from "vitest";
import { api, ApiError, setToken, setRefreshToken } from "../api";

beforeEach(() => {
  vi.restoreAllMocks();
  setToken(null);
  setRefreshToken(null);
  localStorage.clear();
});

describe("ApiError", () => {
  it("stores status, error_id, detail", () => {
    const err = new ApiError("not found", 404, "err_123", { foo: 1 });
    expect(err.message).toBe("not found");
    expect(err.status).toBe(404);
    expect(err.error_id).toBe("err_123");
    expect(err.detail).toEqual({ foo: 1 });
  });
});

describe("api()", () => {
  it("sends GET request and returns json", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ result: "ok" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const data = await api("GET", "/health");
    expect(data).toEqual({ result: "ok" });
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/health",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("includes Authorization header when token is set", async () => {
    setToken("test-token");
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", mockFetch);

    await api("GET", "/me");
    const reqInit = mockFetch.mock.calls[0][1];
    expect(reqInit.headers!["Authorization"]).toBe("Bearer test-token");
  });

  it("throws ApiError on non-ok response", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ error: "bad request", error_id: "e1" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await expect(api("GET", "/test")).rejects.toThrow(ApiError);
    await expect(api("GET", "/test")).rejects.toThrow("bad request");
  });

  it("auto-refreshes on 401 and retries once", async () => {
    let callCount = 0;
    const mockFetch = vi.fn().mockImplementation(async (url: string, opts: any) => {
      callCount++;
      if (url === "/api/v1/auth/refresh") {
        return {
          ok: true,
          json: () => Promise.resolve({ success: true, access_token: "new-token", refresh_token: "new-refresh" }),
        };
      }
      if (callCount === 1) {
        return {
          ok: false,
          status: 401,
          json: () => Promise.resolve({}),
        };
      }
      return {
        ok: true,
        json: () => Promise.resolve({ result: "retried" }),
      };
    });
    vi.stubGlobal("fetch", mockFetch);
    setToken("old-token");
    setRefreshToken("rt");

    const data = await api("GET", "/chat/list");
    expect(data).toEqual({ result: "retried" });
    expect(callCount).toBe(3);
  });
});
