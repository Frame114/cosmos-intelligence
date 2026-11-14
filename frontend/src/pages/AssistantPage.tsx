import { BookOpenCheck, MessageSquareText, ShieldAlert, Sparkles, Trash2 } from "lucide-react";
import { useState } from "react";
import { apiRequest, toPage } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../components/StatePanel";
import { useApiQuery } from "../hooks/useApiQuery";
import type { PageResult, ResearchConversation } from "../types";

export function AssistantPage() {
  const conversations = useApiQuery<PageResult<ResearchConversation>>("/api/v1/research/conversations?page=1&page_size=20");
  const [deleting, setDeleting] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState("");
  const items = conversations.data ? toPage(conversations.data).items : [];

  async function remove(id: string) {
    setDeleting(id);
    setMutationError("");
    try {
      await apiRequest<void>(`/api/v1/research/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });
      conversations.refresh();
    } catch (error) {
      setMutationError(error instanceof Error ? error.message : "The conversation could not be removed.");
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="RESEARCH / EVIDENCE ASSISTANT" title="Ask with evidence." description="Research tools are being prepared to answer from validated Cosmos records and attach source citations." />
      <section className="panel assistant-gate" aria-labelledby="assistant-gate-title">
        <span className="assistant-gate-icon"><ShieldAlert size={23} aria-hidden="true" /></span>
        <div>
          <p className="eyebrow">GENERATION DISABLED</p>
          <h2 id="assistant-gate-title">Policy review is still required</h2>
          <p>Generated answers based on NASA material remain off until the required attribution and usage review is approved. No question will be sent to an AI provider from this page.</p>
        </div>
      </section>
      <div className="content-grid-two">
        <section className="panel">
          <div className="feature-icon-card"><BookOpenCheck size={19} aria-hidden="true" /></div>
          <h2>Grounded in stored records</h2>
          <p className="panel-copy">When available, research answers will use records already validated by Cosmos, preserve their retrieval times, and cite source material used for each claim.</p>
        </section>
        <section className="panel">
          <div className="feature-icon-card feature-icon-amber"><Sparkles size={19} aria-hidden="true" /></div>
          <h2>Uncertainty stays visible</h2>
          <p className="panel-copy">The assistant will mark gaps in the evidence and separate source observations from model-written summaries. It will not replace NASA forecasts or scientific advice.</p>
        </section>
      </div>
      <section className="panel report-list-panel" aria-label="Research conversations">
        <div className="section-title-row"><div><h2>Your conversations</h2><p>Conversation records are private to the signed-in account.</p></div><span className="source-pill"><MessageSquareText size={13} aria-hidden="true" /> Owner scoped</span></div>
        {conversations.pending && items.length === 0 && <LoadingState label="Loading conversations…" />}
        {conversations.error && items.length === 0 && <ErrorState error={conversations.error} onRetry={conversations.refresh} />}
        {mutationError && <p className="field-error" role="alert">{mutationError}</p>}
        {!conversations.pending && !conversations.error && items.length === 0 && <EmptyState title="No conversations saved">The assistant is not accepting questions while policy review is pending.</EmptyState>}
        {items.length > 0 && <div className="report-list">{items.map((item) => (
          <article className="report-card" key={item.id}>
            <div className="report-icon"><MessageSquareText size={18} aria-hidden="true" /></div>
            <div className="report-card-main"><h3>{item.title || "Research conversation"}</h3><small>Updated {new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(item.updated_at))}</small></div>
            <button className="icon-button" type="button" disabled={deleting === item.id} onClick={() => void remove(item.id)} aria-label={`Delete ${item.title || "conversation"}`}><Trash2 size={16} aria-hidden="true" /></button>
          </article>
        ))}</div>}
      </section>
    </div>
  );
}
