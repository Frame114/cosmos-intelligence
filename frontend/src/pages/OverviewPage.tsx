import { ArrowRight, Activity, Globe2, Orbit, Sparkles, Telescope } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { encodeQuery, toPage } from "../api/client";
import { Freshness, MetricCard, ProvenanceLine, SectionTitle, formatDate } from "../components/DataComponents";
import { EmptyState, ErrorState, LoadingState } from "../components/StatePanel";
import { PageHeader } from "../components/PageHeader";
import { SafeMarkup } from "../components/SafeMarkup";
import { safeNasaUrl } from "../api/client";
import { useApiQuery } from "../hooks/useApiQuery";
import type { ApodRecord, AsteroidRecord, EarthEvent, PageResult, SpaceWeatherEvent } from "../types";

function RecordMetric({ label, result }: { label: string; result: PageResult<unknown> }) {
  const count = result.total ?? result.items.length;
  return <span className="metric-inline-count">{count.toLocaleString()} {label}</span>;
}

function ApodFeature() {
  const [imageFailed, setImageFailed] = useState(false);
  const resource = useApiQuery<ApodRecord | PageResult<ApodRecord>>(
    `/api/v1/astronomy/apod${encodeQuery({ page: 1, page_size: 1 })}`,
  );
  const result = resource.data ? toPage(resource.data) : undefined;
  const record = result?.items[0];
  const imageUrl = safeNasaUrl(record?.hdurl || record?.url);

  return (
    <section className="panel apod-feature" aria-labelledby="apod-feature-title">
      <div className="panel-heading">
        <div><p className="eyebrow">ASTRONOMY PICTURE OF THE DAY</p><h2 id="apod-feature-title">A window into the universe</h2></div>
        <Link className="text-link" to="/astronomy">Explore astronomy <ArrowRight size={14} aria-hidden="true" /></Link>
      </div>
      {resource.pending && !record && <LoadingState label="Retrieving NASA astronomy record…" />}
      {resource.error && !record && <ErrorState error={resource.error} onRetry={resource.refresh} />}
      {!resource.pending && !resource.error && !record && <EmptyState title="No APOD record available" />}
      {record && (
        <div className="apod-feature-body">
          <div className="apod-image-frame">
            {record.media_type === "image" && imageUrl && !imageFailed ? (
              <img src={imageUrl} alt={record.alt || "NASA astronomy image; descriptive alt text was not supplied."} loading="lazy" onError={() => setImageFailed(true)} />
            ) : (
              <div className="media-fallback"><Telescope size={30} aria-hidden="true" /><span>{record.media_type === "video" ? "Video record" : "Media preview unavailable"}</span></div>
            )}
            <span className="image-date-tag">{formatDate(record.date)}</span>
          </div>
          <div className="apod-feature-copy">
            <div className="feature-title-row"><h3>{record.title}</h3><Freshness value={result?.freshness} retrievedAt={result?.retrieved_at || record.retrieved_at} /></div>
            <div className="clamp-copy"><SafeMarkup value={record.explanation} fallback="NASA has not supplied an explanation for this record." /></div>
            <div className="feature-meta"><span>{record.media_type.toUpperCase()}</span>{record.credit && <span>{record.credit}</span>}{record.copyright && <span>© {record.copyright}</span>}</div>
            <ProvenanceLine provenance={record.provenance} sourceUrl={record.permalink || record.page_url} retrievedAt={record.retrieved_at} />
            <Link className="button button-primary button-small" to={`/astronomy?date=${encodeURIComponent(record.date)}`}>Open record <ArrowRight size={14} /></Link>
          </div>
        </div>
      )}
    </section>
  );
}

export function OverviewPage() {
  const asteroidQuery = useApiQuery<PageResult<AsteroidRecord> | AsteroidRecord[]>("/api/v1/asteroids?page=1&page_size=5");
  const weatherQuery = useApiQuery<PageResult<SpaceWeatherEvent> | SpaceWeatherEvent[]>("/api/v1/space-weather/events?page=1&page_size=5");
  const earthQuery = useApiQuery<PageResult<EarthEvent> | EarthEvent[]>("/api/v1/earth-events?status=open&page=1&page_size=5");

  const asteroids = asteroidQuery.data ? toPage(asteroidQuery.data) : undefined;
  const weather = weatherQuery.data ? toPage(weatherQuery.data) : undefined;
  const earth = earthQuery.data ? toPage(earthQuery.data) : undefined;
  const now = new Date();

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="MISSION CONTROL / OVERVIEW"
        title="Explore the cosmos."
        description="A living view of astronomy, near-Earth objects, and events across our planet."
        actions={<span className="date-chip"><span className="status-dot" aria-hidden="true" />{new Intl.DateTimeFormat(undefined, { dateStyle: "full", timeZone: "UTC" }).format(now)} UTC</span>}
      />

      <div className="metric-grid">
        <MetricCard label="Asteroid records" value={asteroids ? <RecordMetric label="objects" result={asteroids} /> : "—"} detail={asteroidQuery.error ? "Source unavailable" : "Near-Earth object catalogue"} icon={<Orbit size={17} />} tone="blue" />
        <MetricCard label="Space-weather records" value={weather ? <RecordMetric label="events" result={weather} /> : "—"} detail={weatherQuery.error ? "Source unavailable" : "DONKI event catalogue"} icon={<Activity size={17} />} tone="cyan" />
        <MetricCard label="Open Earth events" value={earth ? <RecordMetric label="events" result={earth} /> : "—"} detail={earthQuery.error ? "Source unavailable" : "NASA EONET curated feed"} icon={<Globe2 size={17} />} tone="amber" />
        <MetricCard label="Research assistant" value={<span className="metric-status">Policy gated</span>} detail="Generated answers remain disabled" icon={<Sparkles size={17} />} tone="green" />
      </div>

      <ApodFeature />

      <div className="content-grid-two">
        <section className="panel" aria-labelledby="near-earth-title">
          <SectionTitle title="Near-Earth objects" detail="Records available from the application data store" action={<Link className="text-link" to="/asteroids">View explorer <ArrowRight size={14} /></Link>} />
          {asteroidQuery.pending && !asteroids && <LoadingState label="Loading asteroid records…" />}
          {asteroidQuery.error && !asteroids && <ErrorState error={asteroidQuery.error} onRetry={asteroidQuery.refresh} />}
          {asteroids && asteroids.items.length === 0 && <EmptyState title="No asteroid records stored" />}
          {asteroids && asteroids.items.length > 0 && (
            <div className="compact-list">
              {asteroids.items.slice(0, 4).map((item) => (
                <Link className="compact-record" key={item.neo_id} to={`/asteroids?neo_id=${encodeURIComponent(item.neo_id)}`}>
                  <span className="record-symbol asteroid-symbol">◉</span>
                  <span className="compact-record-main"><strong>{item.name}</strong><small>{item.neo_id}</small></span>
                  <span className="compact-record-end">{item.potentially_hazardous === null || item.potentially_hazardous === undefined ? "Flag unavailable" : item.potentially_hazardous ? "Source flagged" : "Not flagged"}<ArrowRight size={14} /></span>
                </Link>
              ))}
            </div>
          )}
          {asteroidQuery.error && asteroids && <div className="stale-inline">Refresh failed; showing the previous result.</div>}
        </section>

        <section className="panel" aria-labelledby="weather-title">
          <SectionTitle title="Recent space weather" detail="DONKI event records" action={<Link className="text-link" to="/space-weather">View timeline <ArrowRight size={14} /></Link>} />
          {weatherQuery.pending && !weather && <LoadingState label="Loading space-weather records…" />}
          {weatherQuery.error && !weather && <ErrorState error={weatherQuery.error} onRetry={weatherQuery.refresh} />}
          {weather && weather.items.length === 0 && <EmptyState title="No recent events in the application store" />}
          {weather && weather.items.length > 0 && (
            <div className="compact-list">
              {weather.items.slice(0, 4).map((item, index) => (
                <div className="compact-record compact-record-static" key={`${item.event_id || item.activity_id || item.event_type}-${index}`}>
                  <span className="record-symbol weather-symbol">✳</span>
                  <span className="compact-record-main"><strong>{item.title || item.event_type}</strong><small>{item.event_type} · {formatDate(item.start_time)}</small></span>
                  <span className="event-type-tag">{item.event_type}</span>
                </div>
              ))}
            </div>
          )}
          {weatherQuery.error && weather && <div className="stale-inline">Refresh failed; showing the previous result.</div>}
        </section>
      </div>

      <div className="bottom-callout">
        <div className="callout-icon"><Sparkles size={18} aria-hidden="true" /></div>
        <div><strong>Research, with receipts.</strong><p>Every record keeps a link to its NASA source and the time it was retrieved.</p></div>
        <Link to="/assistant" className="button button-secondary">Explore research tools <ArrowRight size={14} /></Link>
      </div>
    </div>
  );
}
