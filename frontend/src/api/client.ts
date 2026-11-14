import type { PageResult, ProblemDetails } from "../types";

let bearerToken: string | undefined;

export function setApiBearerToken(value: string): void {
  bearerToken = value.trim() || undefined;
}

function localDevelopmentIdentity(): string {
  try {
    const candidate = window.sessionStorage.getItem("cosmos-dev-user") || "local-developer";
    return /^[A-Za-z0-9._@-]{1,128}$/.test(candidate) ? candidate : "local-developer";
  } catch {
    return "local-developer";
  }
}

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly requestId?: string;
  readonly retryable?: boolean;

  constructor(status: number, problem: ProblemDetails, fallback: string) {
    super(problem.detail || problem.title || fallback);
    this.name = "ApiError";
    this.status = status;
    this.code = problem.code;
    this.requestId = problem.request_id;
    this.retryable = problem.retryable;
  }
}

export function makeRequestId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `ci-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  if (!path.startsWith("/") || path.startsWith("//")) {
    throw new Error("API requests must use an application-relative path.");
  }

  const response = await fetch(path, {
    ...options,
    headers: {
      Accept: "application/json, application/problem+json",
      "X-Request-ID": makeRequestId(),
      "X-Dev-User": localDevelopmentIdentity(),
      ...(bearerToken ? { Authorization: `Bearer ${bearerToken}` } : {}),
      ...options.headers,
    },
    credentials: "same-origin",
  });

  if (!response.ok) {
    let problem: ProblemDetails = {};
    try {
      problem = (await response.json()) as ProblemDetails;
    } catch {
      problem = {};
    }
    throw new ApiError(response.status, problem, `The request failed (${response.status}).`);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, { method: "GET", signal });
}

export function toPage<T>(value: PageResult<T> | T[] | { results?: T[] } | T): PageResult<T> {
  if (Array.isArray(value)) return { items: value, total: value.length };
  if (value && typeof value === "object") {
    if ("items" in value && Array.isArray(value.items)) return value as PageResult<T>;
    if ("results" in value && Array.isArray(value.results)) {
      return { items: value.results as T[], total: value.results.length };
    }
  }
  return { items: [value as T], total: 1 };
}

export function encodeQuery(values: Record<string, string | number | boolean | null | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function safeNasaUrl(value?: string | null): string | undefined {
  if (!value) return undefined;
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    const trusted = host === "nasa.gov" || host.endsWith(".nasa.gov");
    return url.protocol === "https:" && trusted ? url.toString() : undefined;
  } catch {
    return undefined;
  }
}
