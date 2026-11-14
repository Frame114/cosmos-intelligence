import { ArrowLeft, ArrowRight, ArrowUpRight, BookmarkCheck, BookmarkPlus, Clock3, ExternalLink, ShieldCheck } from "lucide-react";
import { useState, type ReactNode } from "react";
import { apiRequest } from "../api/client";
import type { Provenance } from "../types";
import { safeNasaUrl } from "../api/client";

export function MetricCard({
  label,
  value,
  detail,
  icon,
  tone = "blue",
}: {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  icon: ReactNode;
  tone?: "blue" | "cyan" | "amber" | "green";
}) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <div className="metric-top"><span>{label}</span><span className="metric-icon">{icon}</span></div>
      <div className="metric-value">{value}</div>
      {detail && <div className="metric-detail">{detail}</div>}
    </article>
  );
}

export function SourcePill({ source }: { source?: string }) {
  return <span className="source-pill"><ShieldCheck size={12} aria-hidden="true" />{source || "NASA source"}</span>;
}

export function Freshness({ value, retrievedAt }: { value?: string; retrievedAt?: string }) {
  const label = value === "stale" ? "Stale" : value === "current" ? "Current" : "Last retrieved";
  return (
    <span className={`freshness freshness-${value || "unknown"}`} title={retrievedAt ? `Retrieved ${formatDateTime(retrievedAt)}` : "Retrieval time not available"}>
      <Clock3 size={12} aria-hidden="true" />{label}
    </span>
  );
}

export function ProvenanceLine({ provenance, sourceUrl, retrievedAt }: {
  provenance?: Provenance;
  sourceUrl?: string;
  retrievedAt?: string;
}) {
  const href = safeNasaUrl(sourceUrl || provenance?.source_url);
  const when = retrievedAt || provenance?.retrieved_at;
  return (
    <div className="provenance-line">
      <SourcePill source={provenance?.source} />
      {when && <span className="provenance-time">Retrieved {formatDateTime(when)}</span>}
      {provenance?.upstream_id && <span className="provenance-id">ID {provenance.upstream_id}</span>}
      {href ? <a href={href} target="_blank" rel="noreferrer">Source <ExternalLink size={12} aria-hidden="true" /></a> : <span className="provenance-no-link">Source link unavailable</span>}
    </div>
  );
}

export function SectionTitle({ title, detail, action }: { title: string; detail?: string; action?: ReactNode }) {
  return (
    <div className="section-title-row">
      <div><h2>{title}</h2>{detail && <p>{detail}</p>}</div>
      {action}
    </div>
  );
}

export function SafeExternalLink({ href, children, className = "" }: { href?: string | null; children: ReactNode; className?: string }) {
  const safeHref = safeNasaUrl(href);
  if (!safeHref) return <span className={`link-unavailable ${className}`}>{children}</span>;
  return <a className={className} href={safeHref} target="_blank" rel="noreferrer">{children}<ArrowUpRight size={13} aria-hidden="true" /></a>;
}

export function formatDate(value?: string | null): string {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeZone: "UTC" }).format(date);
}

export function formatDateTime(value?: string | null): string {
  if (!value) return "Time unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date) + " UTC";
}

export function numberOrDash(value?: number | null, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(value);
}

export function SaveRecordButton({
  sourceCode,
  upstreamId,
  label = "Save record",
}: {
  sourceCode: "APOD" | "NEOWS" | "DONKI" | "EONET" | "NASA_MEDIA";
  upstreamId?: string;
  label?: string;
}) {
  const [saved, setSaved] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function save() {
    if (!upstreamId || pending || saved) return;
    setPending(true);
    setError("");
    try {
      await apiRequest("/api/v1/saved-records", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_code: sourceCode, upstream_id: upstreamId }),
      });
      setSaved(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The record could not be saved.");
    } finally {
      setPending(false);
    }
  }

  return (
    <span className="save-record-control">
      <button className="button button-quiet button-small" type="button" onClick={save} disabled={!upstreamId || pending || saved}>
        {saved ? <BookmarkCheck size={14} aria-hidden="true" /> : <BookmarkPlus size={14} aria-hidden="true" />}
        {pending ? "Saving…" : saved ? "Saved" : label}
      </button>
      {error && <span className="save-record-error" role="status">{error}</span>}
    </span>
  );
}

export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  if (pageCount < 2) return null;
  return (
    <nav className="pagination-bar" aria-label="Result pages">
      <span>Page {page} of {pageCount} · {total.toLocaleString()} records</span>
      <div>
        <button className="button button-quiet button-small" type="button" onClick={() => onPageChange(page - 1)} disabled={page <= 1} aria-label="Previous page"><ArrowLeft size={13} /> Previous</button>
        <button className="button button-quiet button-small" type="button" onClick={() => onPageChange(page + 1)} disabled={page >= pageCount} aria-label="Next page">Next <ArrowRight size={13} /></button>
      </div>
    </nav>
  );
}
