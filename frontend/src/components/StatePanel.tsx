import { AlertTriangle, LoaderCircle, RefreshCw, SearchX } from "lucide-react";
import type { ReactNode } from "react";

export function LoadingState({ label = "Loading source data…" }: { label?: string }) {
  return (
    <div className="state-panel state-loading" role="status" aria-live="polite">
      <LoaderCircle className="spin" size={21} aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: Error; onRetry: () => void }) {
  const status = "status" in error && typeof error.status === "number" ? error.status : undefined;
  const title = status === 401 || status === 403 ? "Sign-in required" : "Source unavailable";
  const message = status === 401 || status === 403
    ? "This view requires an account. Public NASA data remains available."
    : error.message || "The service did not return a usable response.";
  return (
    <div className="state-panel state-error" role="alert">
      <span className="state-icon error-icon"><AlertTriangle size={17} aria-hidden="true" /></span>
      <div className="state-copy"><strong>{title}</strong><span>{message}</span></div>
      <button className="button button-quiet button-small" onClick={onRetry} type="button">
        <RefreshCw size={14} aria-hidden="true" /> Retry
      </button>
    </div>
  );
}

export function EmptyState({
  title = "No records found",
  children = "Try a different filter or check again after the next data refresh.",
  action,
}: {
  title?: string;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="state-panel state-empty">
      <span className="state-icon empty-icon"><SearchX size={19} aria-hidden="true" /></span>
      <div className="state-copy"><strong>{title}</strong><span>{children}</span></div>
      {action}
    </div>
  );
}

export function StaleNotice({ updatedAt }: { updatedAt?: number }) {
  return (
    <div className="stale-notice" role="status">
      <AlertTriangle size={14} aria-hidden="true" />
      <span>Refresh failed. Showing the last successful result{updatedAt ? ` from ${new Date(updatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", timeZone: "UTC" })} UTC` : ""}.</span>
    </div>
  );
}
