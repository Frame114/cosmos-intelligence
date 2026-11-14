import { FileText, Trash2 } from "lucide-react";
import { useState } from "react";
import { apiRequest, toPage } from "../api/client";
import { ProvenanceLine, formatDate } from "../components/DataComponents";
import { PageHeader } from "../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../components/StatePanel";
import { useApiQuery } from "../hooks/useApiQuery";
import type { PageResult, ReportRecord } from "../types";

export function ReportsPage() {
  const resource = useApiQuery<PageResult<ReportRecord> | ReportRecord[]>("/api/v1/reports?page=1&page_size=20");
  const result = resource.data ? toPage(resource.data) : undefined;
  const [deleting, setDeleting] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState("");

  async function remove(id: string) {
    setDeleting(id);
    setMutationError("");
    try {
      await apiRequest<void>(`/api/v1/reports/${encodeURIComponent(id)}`, { method: "DELETE" });
      resource.refresh();
    } catch (error) {
      setMutationError(error instanceof Error ? error.message : "The report could not be removed.");
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="WORKSPACE / REPORTS" title="Research reports" description="Review saved, evidence-linked reports created in your account." />
      <section className="panel report-list-panel" aria-label="Saved reports">
        <div className="section-title-row"><div><h2>Your reports</h2><p>Reports are private to the account that created them.</p></div><span className="source-pill"><FileText size={13} aria-hidden="true" /> Owner scoped</span></div>
        {resource.pending && <LoadingState label="Loading saved reports…" />}
        {resource.error && <ErrorState error={resource.error} onRetry={resource.refresh} />}
        {mutationError && <p className="field-error" role="alert">{mutationError}</p>}
        {result && result.items.length === 0 && <EmptyState title="No saved reports yet">Report generation is disabled while the required NASA policy review is pending. Existing reports stay private here.</EmptyState>}
        {result && result.items.length > 0 && <div className="report-list">{result.items.map((report) => (
          <article className="report-card" key={report.id}>
            <div className="report-icon"><FileText size={19} aria-hidden="true" /></div>
            <div className="report-card-main"><h3>{report.title || "Research report"}</h3><p>{report.question || "No question summary was included."}</p><small>{formatDate(report.generated_at)}{report.model_id ? ` · ${report.model_id}` : ""}</small>
              {report.structured_answer && <pre className="report-answer">{JSON.stringify(report.structured_answer, null, 2)}</pre>}
              {report.citations?.map((citation, index) => <ProvenanceLine key={`${report.id}-${index}`} sourceUrl={citation.source_url} provenance={{ source: citation.source || "Evidence source", upstream_id: citation.upstream_id, source_url: citation.source_url, retrieved_at: citation.retrieved_at }} />)}
            </div>
            <button className="icon-button" type="button" disabled={deleting === report.id} onClick={() => void remove(report.id)} aria-label={`Delete ${report.title || "report"}`}><Trash2 size={16} aria-hidden="true" /></button>
          </article>
        ))}</div>}
      </section>
    </div>
  );
}
