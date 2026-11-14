import { Bookmark, Trash2 } from "lucide-react";
import { useState } from "react";
import { apiRequest, toPage } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { ProvenanceLine, formatDateTime } from "../components/DataComponents";
import { EmptyState, ErrorState, LoadingState } from "../components/StatePanel";
import { useApiQuery } from "../hooks/useApiQuery";
import type { PageResult, SavedRecord } from "../types";

export function SavedRecordsPage() {
  const resource = useApiQuery<PageResult<SavedRecord>>("/api/v1/saved-records?page=1&page_size=50");
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const records = resource.data ? toPage(resource.data).items : [];

  async function remove(id: string) {
    setDeleting(id);
    setError("");
    try {
      await apiRequest<void>(`/api/v1/saved-records/${encodeURIComponent(id)}`, { method: "DELETE" });
      resource.refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The saved record could not be removed.");
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="WORKSPACE / SAVED RECORDS" title="Your saved NASA records" description="Keep a private list of source records for your own research workspace." />
      <section className="panel report-list-panel" aria-label="Saved NASA records">
        <div className="section-title-row"><div><h2>Saved records</h2><p>Only the signed-in account can list or remove these references.</p></div><span className="source-pill"><Bookmark size={13} aria-hidden="true" /> Owner scoped</span></div>
        {resource.pending && records.length === 0 && <LoadingState label="Loading saved records…" />}
        {resource.error && records.length === 0 && <ErrorState error={resource.error} onRetry={resource.refresh} />}
        {error && <div className="field-error" role="alert">{error}</div>}
        {!resource.pending && !resource.error && records.length === 0 && <EmptyState title="No saved records yet">Use “Save record” on an astronomy, asteroid, space weather, Earth event, or NASA media item to keep it here.</EmptyState>}
        {records.length > 0 && <div className="report-list">{records.map((item) => (
          <article className="report-card" key={item.id}>
            <div className="report-icon"><Bookmark size={18} aria-hidden="true" /></div>
            <div className="report-card-main"><h3>{item.record.title}</h3><p>{item.record.source_code} · {item.record.upstream_id}</p><small>Saved {formatDateTime(item.created_at)}</small><ProvenanceLine provenance={item.record.provenance} sourceUrl={item.record.source_url ?? undefined} retrievedAt={item.record.retrieved_at} /></div>
            <button className="icon-button" type="button" disabled={deleting === item.id} onClick={() => void remove(item.id)} aria-label={`Remove ${item.record.title} from saved records`}><Trash2 size={16} aria-hidden="true" /></button>
          </article>
        ))}</div>}
      </section>
    </div>
  );
}
