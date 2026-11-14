import { ArrowUpRight, CalendarDays, Image as ImageIcon, Video } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { encodeQuery, safeNasaUrl, toPage } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { SafeMarkup } from "../components/SafeMarkup";
import { Freshness, Pagination, ProvenanceLine, SaveRecordButton, formatDate } from "../components/DataComponents";
import { EmptyState, ErrorState, LoadingState } from "../components/StatePanel";
import { useApiQuery } from "../hooks/useApiQuery";
import type { ApodRecord, PageResult } from "../types";

function utcToday() {
  return new Date().toISOString().slice(0, 10);
}

function ApodMedia({ record, media, pageUrl }: { record: ApodRecord; media?: string | null; pageUrl?: string | null }) {
  const [imageFailed, setImageFailed] = useState(false);
  if (record.media_type === "image" && media && !imageFailed) {
    return (
      <img
        src={media}
        alt={record.alt || "NASA astronomy image; descriptive alt text was not supplied."}
        loading="lazy"
        onError={() => setImageFailed(true)}
      />
    );
  }
  return (
    <div className="media-fallback">
      <span className="media-type-icon">{record.media_type === "video" ? <Video size={27} /> : <ImageIcon size={27} />}</span>
      <strong>{record.media_type === "video" ? "Video record" : "Preview unavailable"}</strong>
      {pageUrl && <a href={pageUrl} target="_blank" rel="noreferrer">Open NASA record <ArrowUpRight size={13} /></a>}
    </div>
  );
}

export function AstronomyPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [date, setDate] = useState(searchParams.get("date") || utcToday());
  const [search, setSearch] = useState(searchParams.get("q") || "");
  const [applied, setApplied] = useState({ date: searchParams.get("date") || utcToday(), q: searchParams.get("q") || "" });
  const [page, setPage] = useState(1);
  const path = applied.q
    ? `/api/v1/astronomy/records${encodeQuery({ q: applied.q, page, page_size: 20 })}`
    : `/api/v1/astronomy/apod/${encodeURIComponent(applied.date)}`;
  const resource = useApiQuery<ApodRecord | PageResult<ApodRecord> | ApodRecord[]>(path);

  useEffect(() => {
    const queryDate = searchParams.get("date");
    const queryText = searchParams.get("q");
    if (queryDate) setDate(queryDate);
    if (queryText) setSearch(queryText);
    if (queryDate || queryText) {
      setApplied({ date: queryDate || utcToday(), q: queryText || "" });
      setPage(1);
    }
  }, [searchParams]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next = { date, q: search.trim() };
    setApplied(next);
    setPage(1);
    const params: Record<string, string> = next.q ? { q: next.q } : { date: next.date };
    setSearchParams(params);
  }

  const records = resource.data
    ? Array.isArray(resource.data)
      ? resource.data
      : "items" in resource.data && Array.isArray(resource.data.items)
        ? toPage(resource.data).items
        : [resource.data as ApodRecord]
    : [];

  return (
    <div className="page-stack">
      <PageHeader eyebrow="EXPLORE / ASTRONOMY" title="Astronomy explorer" description="Browse NASA’s daily astronomy records, their explanations, and source provenance." />

      <section className="panel filter-panel" aria-label="Search astronomy records">
        <form className="filter-form astronomy-filters" onSubmit={submit}>
          <label className="field-label" htmlFor="apod-date">APOD date <span className="optional-note">UTC</span>
            <span className="input-with-icon"><CalendarDays size={16} aria-hidden="true" /><input id="apod-date" type="date" value={date} max={utcToday()} onChange={(event) => setDate(event.target.value)} /></span>
          </label>
          <label className="field-label field-search-label" htmlFor="astronomy-search">Search historical records
            <input id="astronomy-search" type="search" placeholder="Try “galaxy” or “eclipse”" value={search} onChange={(event) => setSearch(event.target.value)} maxLength={200} />
          </label>
          <button className="button button-primary" type="submit">Search records</button>
        </form>
        <p className="helper-copy">Historical search uses validated records stored by Cosmos. The NASA APOD guide supports a bounded page size; older records may be absent until ingested.</p>
      </section>

      {resource.pending && records.length === 0 && <LoadingState label="Retrieving astronomy records…" />}
      {resource.error && records.length === 0 && <ErrorState error={resource.error} onRetry={resource.refresh} />}
      {!resource.pending && !resource.error && records.length === 0 && <EmptyState title="No astronomy record for this search" />}
      {resource.error && records.length > 0 && <div className="stale-notice" role="status">Refresh failed; the records below are the last successful result.</div>}

      <div className="astronomy-record-grid">
        {records.map((record) => {
          const media = safeNasaUrl(record.hdurl || record.url);
          const pageUrl = safeNasaUrl(record.permalink || record.page_url);
          return (
            <article className="panel astronomy-record" key={`${record.date}-${record.post_id || record.title}`}>
              <div className="record-media-stage">
                <ApodMedia record={record} media={media} pageUrl={pageUrl} />
              </div>
              <div className="astronomy-record-content">
                <div className="record-headerline"><span>{formatDate(record.date)}</span><Freshness value={resource.data && "freshness" in resource.data ? resource.data.freshness : undefined} retrievedAt={record.retrieved_at} /></div>
                <h2>{record.title}</h2>
                <div className="explanation-copy"><SafeMarkup value={record.explanation} fallback="NASA has not supplied an explanation for this record." /></div>
                <div className="credit-row">{record.credit && <span>{record.credit}</span>}{record.copyright && <span>© {record.copyright}</span>}</div>
                <ProvenanceLine provenance={record.provenance} sourceUrl={record.permalink || record.page_url} retrievedAt={record.retrieved_at} />
                <div className="record-actions">
                  <SaveRecordButton sourceCode="APOD" upstreamId={record.date} />
                  {record.hdurl && safeNasaUrl(record.hdurl) && <a className="button button-secondary button-small" href={safeNasaUrl(record.hdurl)} target="_blank" rel="noreferrer">Open HD image <ArrowUpRight size={13} /></a>}
                  <Link className="button button-quiet button-small" to={`/assistant?record=${encodeURIComponent(record.date)}`}>Ask about this record</Link>
                </div>
              </div>
            </article>
          );
        })}
      </div>
      {applied.q && resource.data && <Pagination page={page} pageSize={20} total={"total" in resource.data ? resource.data.total ?? records.length : records.length} onPageChange={setPage} />}
    </div>
  );
}
