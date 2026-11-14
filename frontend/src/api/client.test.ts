import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiRequest, encodeQuery, safeNasaUrl, setApiBearerToken, toPage } from "./client";

afterEach(() => {
  setApiBearerToken("");
  window.sessionStorage.removeItem("cosmos-dev-user");
  vi.unstubAllGlobals();
});

describe("frontend API helpers", () => {
  it("encodes nonempty query values without including undefined values", () => {
    expect(encodeQuery({ q: "solar flare", page: 2, blank: "", missing: undefined })).toBe("?q=solar+flare&page=2");
  });

  it("normalizes list responses and keeps source allowlisting", () => {
    expect(toPage(["one", "two"])).toEqual({ items: ["one", "two"], total: 2 });
    expect(safeNasaUrl("https://images-api.nasa.gov/item/123")).toContain("images-api.nasa.gov");
    expect(safeNasaUrl("https://example.invalid/image.jpg")).toBeUndefined();
    expect(safeNasaUrl("javascript:alert(1)")).toBeUndefined();
  });

  it("turns problem responses into an API error without exposing other fields", () => {
    const error = new ApiError(503, { detail: "Unavailable", code: "source_down", request_id: "req-1" }, "Fallback");
    expect(error).toBeInstanceOf(Error);
    expect(error.message).toBe("Unavailable");
    expect(error.requestId).toBe("req-1");
    expect(error.status).toBe(503);
  });

  it("keeps the local identity tab scoped and sends a bearer token only from memory", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ authenticated: true }),
    });
    vi.stubGlobal("fetch", fetchMock);
    window.sessionStorage.setItem("cosmos-dev-user", "test-user");
    setApiBearerToken("ephemeral-access-token");

    await expect(apiRequest("/api/v1/auth/session")).resolves.toEqual({ authenticated: true });

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get("X-Dev-User")).toBe("test-user");
    expect(headers.get("Authorization")).toBe("Bearer ephemeral-access-token");
    expect(window.localStorage.getItem("cosmos-oidc-token")).toBeNull();
  });
});
