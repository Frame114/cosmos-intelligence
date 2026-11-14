import { Filter, Image as ImageIcon, Play, Search } from "lucide-react";
import { useState, type FormEvent } from "react";
import { encodeQuery, safeNasaUrl, toPage } from "../api/client";
import { Freshness, Pagination, ProvenanceLine, SaveRecordButton, formatDate } from "../components/DataComponents";
import { PageHeader } from "../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../components/StatePanel";
import { useApiQuery } from "../hooks/useApiQuery";
import type { MediaRecord, PageResult } from "../types";

interface MediaSearchItem extends MediaRecord {
  retrieved_at?: string;
}

function MediaCard({ item }: { item: MediaSearchItem }) {
  const [expanded, setExpanded] = useState(false);
  const thumbnail = safeNasaUrl(item.thumbnail_url);
  const detail = safeNasaUrl(item.detail_url || item.provenance?.source_url);
  const detailPath = expanded ? `/api/v1/media/${encodeURIComponent(item.nasa_id)}` : null;
  const detailResource = useApiQuery<MediaSearchItem>(detailPath);
  const Icon = item.media_type === "video" ? Play : ImageIcon;

  return (
    <article className="media-card">
      <div className="media-card-image">
        {thumbnail ? <img src={thumbnail} alt="" loading="lazy" /> : <div className="media-fallback"><Icon size={27} aria-hidden="true" /><span>Preview unavailable</span></div>}
        <span className="media-type-tag">{item.media_type}</span>
      </div>
      <div className="media-card-content">
        <div className="media-card-heading"><h2>{item.title}</h2><Freshness value="unknown" retrievedAt={item.retrieved_at} /></div>
        <p>{item.description || "NASA has not supplied a description for this item."}</p>
        <div className="media-card-meta">
          {item.date_created && <span>{formatDate(item.date_created)}</span>}
          {item.creators?.length ? <span>{item.creators.slice(0, 3).join(", ")}</span> : null}
        </div>
        {item.rights_note && <p className="rights-note">{item.rights_note}</p>}
        <ProvenanceLine provenance={item.provenance} sourceUrl={detail} retrievedAt={item.retrieved_at} />
        <div className="record-actions"><SaveRecordButton sourceCode="NASA_MEDIA" upstreamId={item.nasa_id} /><button className="text-link metadata-toggle" type="button" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>{expanded ? "Hide metadata" : "More metadata"}</button></div>
        {expanded && detailResource.pending && <LoadingState label="Loading NASA media details…" />}
        {expanded && detailResource.error && <ErrorState error={detailResource.error} onRetry={detailResource.refresh} />}
        {expanded && detailResource.data && <div className="media-detail-extra">
          {detailResource.data.description_508 && <p><strong>Accessibility description</strong>{detailResource.data.description_508}</p>}
          {detailResource.data.keywords?.length ? <p><strong>NASA keywords</strong>{detailResource.data.keywords.slice(0, 20).join(" · ")}</p> : null}
          {safeNasaUrl(detailResource.data.asset_manifest_url) && <a className="text-link" href={safeNasaUrl(detailResource.data.asset_manifest_url)} target="_blank" rel="noreferrer">NASA asset manifest</a>}
        </div>}
      </div>
    </article>
  );
}

export function MediaPage() {
  const [draft, setDraft] = useState({ query: "", mediaType: "", from: "", to: "" });
  const [applied, setApplied] = useState<typeof draft | null>(null);
  const [page, setPage] = useState(1);
  const invalidYears = Boolean(draft.from && draft.to && draft.from > draft.to);
  const path = applied
    ? `/api/v1/media${encodeQuery({ q: applied.query, media_type: applied.mediaType, year_start: applied.from, year_end: applied.to, page, page_size: 24 })}`
    : null;
  const resource = useApiQuery<PageResult<MediaSearchItem> | MediaSearchItem[]>(path);
  const result = resource.data ? toPage(resource.data) : undefined;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = draft.query.trim();
    if (!query || invalidYears) return;
    setApplied({ ...draft, query });
    setPage(1);
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="EXPLORE / NASA MEDIA" title="NASA media library" description="Search NASA’s image and video metadata while keeping item-level credits and source links close to the media." />
      <section className="panel filter-panel">
        <form className="filter-form media-filters" onSubmit={submit}>
          <label className="field-label" htmlFor="media-query">Search NASA media<input id="media-query" value={draft.query} maxLength={200} onChange={(event) => setDraft({ ...draft, query: event.target.value })} placeholder="Moon, Apollo, Mars…" /></label>
          <label className="field-label" htmlFor="media-type">Media type<select id="media-type" value={draft.mediaType} onChange={(event) => setDraft({ ...draft, mediaType: event.target.value })}><option value="">All types</option><option value="image">Images</option><option value="video">Videos</option><option value="audio">Audio</option></select></label>
          <label className="field-label" htmlFor="media-year-from">Year from<input id="media-year-from" inputMode="numeric" pattern="[0-9]{4}" maxLength={4} value={draft.from} onChange={(event) => setDraft({ ...draft, from: event.target.value })} placeholder="1969" /></label>
          <label className="field-label" htmlFor="media-year-to">Year to<input id="media-year-to" inputMode="numeric" pattern="[0-9]{4}" maxLength={4} value={draft.to} onChange={(event) => setDraft({ ...draft, to: event.target.value })} placeholder="2026" /></label>
          <button className="button button-primary" type="submit" disabled={!draft.query.trim() || invalidYears}><Search size={15} aria-hidden="true" /> Search media</button>
        </form>
        {invalidYears && <p className="field-error" role="alert">The starting year must not be later than the ending year.</p>}
        <p className="helper-copy"><Filter size={13} aria-hidden="true" /> Results contain descriptive metadata and links; Cosmos does not mirror NASA media files.</p>
      </section>
      <section className="panel media-results-panel" aria-label="NASA media search results">
        <div className="section-title-row"><div><h2>Search results</h2><p>{result ? `${result.total ?? result.items.length} records returned` : "Search the official NASA Media Library."}</p></div></div>
        {!applied && <EmptyState title="Start with a search">Enter a topic to search the NASA Media Library. No sample results are shown.</EmptyState>}
        {resource.pending && <LoadingState label="Searching NASA media metadata…" />}
        {resource.error && <ErrorState error={resource.error} onRetry={resource.refresh} />}
        {result && result.items.length === 0 && !resource.pending && <EmptyState title="No media matched this search" />}
        {result && result.items.length > 0 && <><div className="media-grid">{result.items.map((item) => <MediaCard item={item} key={item.nasa_id} />)}</div><Pagination page={page} pageSize={24} total={result.total ?? result.items.length} onPageChange={setPage} /></>}
      </section>
    </div>
  );
}
