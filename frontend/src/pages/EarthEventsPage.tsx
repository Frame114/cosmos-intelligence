import { CircleDot, ExternalLink, Filter, Image as ImageIcon, MapPin, Newspaper, X } from "lucide-react";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { CircleMarker, MapContainer, Polygon, Popup, TileLayer, WMSTileLayer, useMap } from "react-leaflet";
import { apiRequest, encodeQuery, safeNasaUrl, toPage } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { Pagination, ProvenanceLine, SaveRecordButton, SectionTitle, formatDate } from "../components/DataComponents";
import { EmptyState, ErrorState, LoadingState } from "../components/StatePanel";
import { useApiQuery } from "../hooks/useApiQuery";
import type { EarthEvent, EarthEventCoverage, EonetGeometry, PageResult } from "../types";
import "leaflet/dist/leaflet.css";

interface MappedEvent {
  id: string;
  title: string;
  position?: [number, number];
  polygon?: [number, number][];
}

function coordinatePair(value: unknown): [number, number] | undefined {
  if (!Array.isArray(value) || value.length < 2) return undefined;
  const longitude = Number(value[0]);
  const latitude = Number(value[1]);
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude) || Math.abs(longitude) > 180 || Math.abs(latitude) > 90) return undefined;
  return [latitude, longitude];
}

function latestGeometry(geometries?: EonetGeometry[] | null): MappedEvent["position"] | MappedEvent["polygon"] {
  const item = geometries?.[geometries.length - 1];
  if (!item?.coordinates) return undefined;
  if (item.type === "Point") return coordinatePair(item.coordinates);
  if (item.type === "Polygon" && Array.isArray(item.coordinates)) {
    const ring = item.coordinates[0];
    if (!Array.isArray(ring)) return undefined;
    const points = ring.map(coordinatePair).filter((point): point is [number, number] => Boolean(point));
    return points.length >= 3 ? points : undefined;
  }
  return undefined;
}

function SelectedMarker({ position }: { position: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(position, Math.max(map.getZoom(), 4), { duration: 0.45 });
  }, [map, position[0], position[1]]);
  return null;
}

function EventMap({ events, selectedId, onSelect, coverage }: { events: EarthEvent[]; selectedId?: string; onSelect: (id: string) => void; coverage?: EarthEventCoverage }) {
  const tileUrl = import.meta.env.VITE_MAP_TILE_URL || "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
  const mapped = events.map((event) => ({ event, geometry: latestGeometry(event.geometry) })).filter((item) => item.geometry);
  const selected = mapped.find((item) => (item.event.event_id || item.event.id) === selectedId);
  const focus = selected?.geometry && Array.isArray(selected.geometry[0]) ? selected.geometry[0] as [number, number] : undefined;

  return (
    <div className="event-map-wrap">
      <MapContainer center={[18, 0]} zoom={1.4} minZoom={1} maxZoom={11} scrollWheelZoom worldCopyJump className="event-map" aria-label="Map of EONET event geometries">
        <TileLayer url={tileUrl} attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>' />
        {coverage?.satellite_imagery && <WMSTileLayer key={`${coverage.satellite_imagery.name}-${coverage.satellite_imagery.date || "latest"}`} url={coverage.satellite_imagery.date ? `${coverage.satellite_imagery.service_url}?TIME=${encodeURIComponent(coverage.satellite_imagery.date)}` : coverage.satellite_imagery.service_url} layers={coverage.satellite_imagery.name} format={coverage.satellite_imagery.format} transparent version="1.1.1" attribution={coverage.satellite_imagery.attribution} />}
        {focus && <SelectedMarker position={focus} />}
        {mapped.map(({ event, geometry }) => {
          const id = event.event_id || event.id || event.title;
          if (!geometry) return null;
          if (Array.isArray(geometry[0])) {
            return <Polygon key={id} positions={geometry as [number, number][]} pathOptions={{ color: id === selectedId ? "#63d4e7" : "#83a9ff", fillOpacity: 0.18, weight: id === selectedId ? 3 : 1.5 }} eventHandlers={{ click: () => onSelect(id) }}><Popup>{event.title}</Popup></Polygon>;
          }
          return <CircleMarker key={id} center={geometry as [number, number]} radius={id === selectedId ? 8 : 5} pathOptions={{ color: "#07111f", fillColor: id === selectedId ? "#e6a451" : "#75d6e5", fillOpacity: 0.95, weight: 2 }} eventHandlers={{ click: () => onSelect(id) }}><Popup><strong>{event.title}</strong><br />{event.categories?.map((category) => typeof category === "string" ? category : category.title).filter(Boolean).join(", ")}</Popup></CircleMarker>;
        })}
      </MapContainer>
      <div className="map-caption"><MapPin size={13} aria-hidden="true" /><span>{mapped.length} event{mapped.length === 1 ? "" : "s"} with mappable geometry · Scroll over the map to zoom; outside it, the wheel scrolls the page.{coverage?.satellite_imagery ? ` NASA ${coverage.satellite_imagery.name} imagery for ${coverage.satellite_imagery.date || "the latest available date"}.` : ""}</span></div>
      {mapped.length === 0 && <div className="map-empty-overlay">No geographic points or polygons in this response.</div>}
    </div>
  );
}

function articleDate(value?: string | null): string {
  const gdelt = value?.match(/^(\d{4})(\d{2})(\d{2})T/);
  return gdelt ? formatDate(`${gdelt[1]}-${gdelt[2]}-${gdelt[3]}`) : formatDate(value);
}

function CoverageReport({ coverage, pending, error, onRetry }: {
  coverage?: EarthEventCoverage;
  pending: boolean;
  error?: string;
  onRetry: () => void;
}) {
  if (pending) return <section className="event-coverage" aria-live="polite"><div className="event-coverage-heading"><Newspaper size={17} /><div><h3>Event report &amp; coverage</h3><p>Loading NASA imagery and related news reports…</p></div></div><LoadingState label="Searching event sources…" /></section>;
  if (error) return <section className="event-coverage" role="status"><div className="event-coverage-heading"><Newspaper size={17} /><div><h3>Event report &amp; coverage</h3><p>{error}</p></div><button className="button button-quiet button-small" type="button" onClick={onRetry}>Retry</button></div></section>;
  if (!coverage) return null;

  const report = coverage.description || `${coverage.title} is listed as an ${coverage.status} event${coverage.categories.length ? ` in ${coverage.categories.join(", ")}` : ""} by NASA EONET.`;
  const hasCoverage = coverage.nasa_images.length > 0 || coverage.related_articles.length > 0;
  return (
    <section className="event-coverage" aria-labelledby={`coverage-${coverage.event_id}`}>
      <div className="event-coverage-heading"><Newspaper size={17} /><div><p className="eyebrow">NASA EONET EVENT BRIEF</p><h3 id={`coverage-${coverage.event_id}`}>{coverage.title}</h3><p>{coverage.categories.join(" · ") || "Natural event"} · {coverage.status} · Last geometry {formatDate(coverage.observed_at)}</p></div></div>
      <p className="event-coverage-summary">{report}</p>
      {coverage.sources.length > 0 && <div className="event-source-links"><strong>Original event sources</strong>{coverage.sources.map((source) => <a key={`${source.id}-${source.url}`} href={source.url || undefined} target="_blank" rel="noreferrer">{source.id}<ExternalLink size={12} /></a>)}</div>}
      {coverage.satellite_imagery && <p className="event-imagery-note"><ImageIcon size={14} /> NASA satellite layer is overlaid on the map for {coverage.satellite_imagery.date || "the latest available date"}. {coverage.satellite_imagery.attribution}.</p>}
      {hasCoverage ? (
        <div className="event-coverage-grid">
          {coverage.related_articles.map((article, index) => <a className="event-coverage-card" href={article.url} key={`${article.url}-${index}`} target="_blank" rel="noreferrer">
            {article.image_url ? <img src={article.image_url} alt="" loading="lazy" referrerPolicy="no-referrer" /> : <div className="event-coverage-placeholder"><Newspaper size={21} /><span>NEWS REPORT</span></div>}
            <div className="event-coverage-card-copy"><strong>{article.title}</strong><span>{article.publisher} · {articleDate(article.published_at)}</span><small>Open related coverage <ExternalLink size={11} /></small></div>
          </a>)}
          {coverage.nasa_images.map((image) => <a className="event-coverage-card" href={safeNasaUrl(image.detail_url) || undefined} key={image.nasa_id} target="_blank" rel="noreferrer">
            {image.thumbnail_url ? <img src={safeNasaUrl(image.thumbnail_url) || undefined} alt="" loading="lazy" referrerPolicy="no-referrer" /> : <div className="event-coverage-placeholder"><ImageIcon size={21} /><span>NASA MEDIA</span></div>}
            <div className="event-coverage-card-copy"><strong>{image.title}</strong><span>NASA Image and Video Library{image.date_created ? ` · ${formatDate(image.date_created)}` : ""}</span><small>View NASA media <ExternalLink size={11} /></small></div>
          </a>)}
        </div>
      ) : <div className="event-coverage-empty"><p>No matching article or NASA media images were returned for this event. The NASA source links above remain available.</p>{coverage.news_search_url && <a className="text-link" href={coverage.news_search_url} target="_blank" rel="noreferrer">Search Google News for this event <ExternalLink size={12} /></a>}</div>}
      <p className="event-coverage-disclaimer">News results are related coverage matched by the event title; they are not independently verified reports about this specific event. News images remain hosted by their publishers. NASA media results are separate library matches and may not depict this event.</p>
    </section>
  );
}

export function EarthEventsPage() {
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("open");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [filters, setFilters] = useState({ category: "", status: "open", start: "", end: "" });
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string>();
  const [coverage, setCoverage] = useState<EarthEventCoverage>();
  const [coveragePending, setCoveragePending] = useState(false);
  const [coverageError, setCoverageError] = useState("");
  const [coverageRetry, setCoverageRetry] = useState(0);
  const path = `/api/v1/earth-events${encodeQuery({ category: filters.category, status: filters.status, start: filters.start, end: filters.end, page, page_size: 100 })}`;
  const resource = useApiQuery<PageResult<EarthEvent> | EarthEvent[]>(path);
  const events = resource.data ? toPage(resource.data).items : [];
  const sorted = [...events].sort((a, b) => (b.opened_at || "").localeCompare(a.opened_at || ""));
  const selected = selectedId ? events.find((event) => (event.event_id || event.id) === selectedId) : undefined;

  useEffect(() => {
    if (!selectedId) {
      setCoverage(undefined);
      setCoveragePending(false);
      setCoverageError("");
      return;
    }
    const controller = new AbortController();
    setCoverage(undefined);
    setCoveragePending(true);
    setCoverageError("");
    void apiRequest<EarthEventCoverage>(`/api/v1/earth-events/${encodeURIComponent(selectedId)}/coverage`, { signal: controller.signal })
      .then((value) => { if (!controller.signal.aborted) setCoverage(value); })
      .catch((cause: unknown) => { if (!controller.signal.aborted) setCoverageError(cause instanceof Error ? cause.message : "Event coverage is unavailable."); })
      .finally(() => { if (!controller.signal.aborted) setCoveragePending(false); });
    return () => controller.abort();
  }, [selectedId, coverageRetry]);

  const selectMapEvent = useCallback((id: string) => {
    setSelectedId(id);
    window.setTimeout(() => document.getElementById(`earth-event-${id}`)?.scrollIntoView({ behavior: "smooth", block: "center" }), 100);
  }, []);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (start && end && start > end) return;
    setFilters({ category: category.trim(), status, start, end });
    setPage(1);
    setSelectedId(undefined);
  }

  const invalidRange = Boolean(start && end && start > end);

  return (
    <div className="page-stack">
      <PageHeader eyebrow="EXPLORE / EARTH EVENTS" title="Earth events" description="Explore NASA EONET’s curated natural-event metadata, geometry, and original source references." actions={<span className="source-pill"><MapPin size={13} /> EONET v3</span>} />
      <section className="panel filter-panel">
        <form className="filter-form earth-filters" onSubmit={submit}>
          <label className="field-label" htmlFor="eonet-category">Category ID<input id="eonet-category" value={category} maxLength={80} onChange={(event) => setCategory(event.target.value)} placeholder="e.g. wildfires" /></label>
          <label className="field-label" htmlFor="eonet-status">Event status<select id="eonet-status" value={status} onChange={(event) => setStatus(event.target.value)}><option value="open">Open</option><option value="closed">Closed</option><option value="all">All</option></select></label>
          <label className="field-label" htmlFor="eonet-start">From <span className="optional-note">UTC</span><input id="eonet-start" type="date" value={start} onChange={(event) => setStart(event.target.value)} /></label>
          <label className="field-label" htmlFor="eonet-end">To <span className="optional-note">UTC</span><input id="eonet-end" type="date" value={end} onChange={(event) => setEnd(event.target.value)} /></label>
          <button className="button button-primary" type="submit"><Filter size={15} /> Filter events</button>
        </form>
        {invalidRange && <p className="field-error" role="alert">The start date must be before or equal to the end date.</p>}
      </section>

      <section className="panel map-panel" aria-label="Earth event map">
        <SectionTitle title="Event geography" detail="Select a marker or event below to synchronize the selection." />
        {resource.pending && events.length === 0 && <LoadingState label="Loading EONET events…" />}
        {resource.error && events.length === 0 && <ErrorState error={resource.error} onRetry={resource.refresh} />}
        {events.length > 0 && <EventMap events={events} selectedId={selectedId} onSelect={selectMapEvent} coverage={coverage} />}
        {events.length === 0 && !resource.pending && !resource.error && <EmptyState title="No events match these filters" />}
        <p className="helper-copy map-attribution-note">Map tiles use the configured tile service; OpenStreetMap attribution is shown on the map. Follow the provider’s usage policy before public deployment.</p>
      </section>

      <section className="panel events-panel" aria-labelledby="earth-event-list-heading">
        <SectionTitle title="Curated event list" detail={`${events.length} records returned · EONET metadata is not an exhaustive census.`} />
        {resource.error && events.length > 0 && <div className="stale-notice" role="status">Refresh failed; showing the previously loaded events.</div>}
        {sorted.length > 0 && (
          <div className="earth-event-list">
            {sorted.map((item) => {
              const id = item.event_id || item.id || item.title;
              const active = id === selectedId;
              return (
                <article id={`earth-event-${id}`} key={id} className={`earth-event-card ${active ? "earth-event-selected" : ""}`}>
                  <button type="button" className="earth-event-main" onClick={() => setSelectedId(active ? undefined : id)} aria-expanded={active}>
                    <span className="event-status-dot" aria-label={item.closed_at || item.status === "closed" ? "Closed event" : "Open event"} />
                    <span><strong>{item.title}</strong><small>{formatDate(item.opened_at)} · {item.status || (item.closed_at ? "closed" : "open")}</small></span>
                    <span className="earth-categories">{item.categories?.map((categoryItem) => typeof categoryItem === "string" ? categoryItem : categoryItem.title).filter(Boolean).join(" · ") || "Category unavailable"}</span>
                  </button>
                  {active && (
                    <div className="earth-event-detail">
                      {item.description && <p>{item.description}</p>}
                      <ProvenanceLine provenance={item.provenance} sourceUrl={item.source_url || item.sources?.[0]?.url} retrievedAt={item.retrieved_at} />
                      <SaveRecordButton sourceCode="EONET" upstreamId={item.event_id || item.id} />
                      {item.geometry?.length ? <p className="geometry-date">Latest geometry observation: {formatDate(item.geometry[item.geometry.length - 1]?.date)}</p> : <p className="geometry-date">No geometry supplied by source.</p>}
                      {safeNasaUrl(item.source_url) && <a className="text-link" href={safeNasaUrl(item.source_url)} target="_blank" rel="noreferrer">Open EONET source <MapPin size={13} /></a>}
                      <CoverageReport coverage={selectedId === id ? coverage : undefined} pending={selectedId === id && coveragePending} error={selectedId === id ? coverageError : ""} onRetry={() => setCoverageRetry((value) => value + 1)} />
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>
      {resource.data && <Pagination page={page} pageSize={100} total={"total" in resource.data ? resource.data.total ?? events.length : events.length} onPageChange={setPage} />}
      {selected && <div className="selection-banner"><CircleDot size={15} /> Selected: {selected.title}<button className="icon-button" aria-label="Clear selected event" onClick={() => setSelectedId(undefined)}><X size={14} /></button></div>}
    </div>
  );
}
