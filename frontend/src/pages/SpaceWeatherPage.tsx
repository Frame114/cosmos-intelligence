import { Activity, ArrowUpRight, CalendarRange, CircleAlert, Clock3, Magnet, Orbit, Radio, Sun, Waves, Zap } from "lucide-react";
import { useState, type FormEvent } from "react";
import { encodeQuery, toPage } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { Pagination, ProvenanceLine, SaveRecordButton, SectionTitle, formatDateTime } from "../components/DataComponents";
import { EmptyState, ErrorState, LoadingState } from "../components/StatePanel";
import { useApiQuery } from "../hooks/useApiQuery";
import type { PageResult, SpaceWeatherEvent } from "../types";

const EVENT_TYPES = ["CME", "CMEAnalysis", "GST", "IPS", "FLR", "SEP", "MPC", "RBE", "HSS"];

function readText(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function cleanMessage(value: string): string {
  return value
    .replace(/\r\n?/g, "\n")
    .replace(/^\s*#{1,6}\s*/gm, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}

function parseNotification(event: SpaceWeatherEvent) {
  const body = readText(event.details?.messageBody) || readText(event.summary) || "";
  const pattern = /(?:^|[\r\n\s])#{0,6}\s*(Message Type|Message Issue Date|Message ID|Activity ID|Summary|Disclaimer|Notes)\s*:\s*/gi;
  const matches = Array.from(body.matchAll(pattern));
  const fields = new Map<string, string>();
  matches.forEach((match, index) => {
    const start = (match.index ?? 0) + match[0].length;
    const end = matches[index + 1]?.index ?? body.length;
    const value = body.slice(start, end).replace(/\s*#{1,6}\s*$/g, "").trim();
    const label = match[1]?.toLowerCase();
    if (label && value && !fields.has(label)) fields.set(label, cleanMessage(value));
  });

  const details = event.details ?? {};
  const fullType = fields.get("message type") || readText(details.messageType) || event.title || "Space weather notification";
  const category = fullType.replace(/^(?:auto-generated\s+)?space weather notification\s*[-:–]?\s*/i, "").trim() || fullType;
  const activityId = fields.get("activity id") || readText(details.activityID) || event.activity_id;
  const summary = fields.get("summary") || (matches.length ? "Notification details are available below." : cleanMessage(body));
  return {
    body: cleanMessage(body),
    category,
    summary,
    messageId: fields.get("message id") || readText(details.messageID) || event.event_id,
    activityId,
    issueTime: fields.get("message issue date") || readText(details.messageIssueTime) || event.start_time || undefined,
    disclaimer: fields.get("disclaimer"),
    notes: fields.get("notes"),
  };
}

function weatherVisual(category: string) {
  const value = category.toLowerCase();
  if (value.includes("flare") || value.includes("coronal mass")) return { Icon: Sun, theme: "solar" };
  if (value.includes("radiation belt") || value.includes("energetic particle")) return { Icon: Zap, theme: "radiation" };
  if (value.includes("geomagnetic")) return { Icon: Magnet, theme: "geomagnetic" };
  if (value.includes("shock") || value.includes("high speed stream")) return { Icon: Waves, theme: "solar-wind" };
  if (value.includes("crossing") || value.includes("cme")) return { Icon: Orbit, theme: "orbit" };
  if (value.includes("notification")) return { Icon: Radio, theme: "notification" };
  return { Icon: CircleAlert, theme: "general" };
}

function extractMeasurements(summary: string) {
  const pattern = /\b(greater than|above|approximately|around|reaching|maximum(?: sustained)? speed of|over)\s+([\d,]+(?:\.\d+)?)\s*(km\/s|pfu|mev|nt)\b/gi;
  const measurements: Array<{ value: string; label: string }> = [];
  for (const match of summary.matchAll(pattern)) {
    const qualifier = match[1]?.toLowerCase() || "";
    const amount = match[2] || "";
    const unit = (match[3] || "").toLowerCase();
    const prefix = ["greater than", "above", "over"].includes(qualifier) ? ">" : qualifier === "approximately" || qualifier === "around" ? "≈" : "";
    const label = unit === "pfu" ? "Particle flux" : unit === "mev" ? "Particle energy" : unit === "km/s" ? "Speed" : "Magnetic field";
    const value = `${prefix}${amount} ${unit === "mev" ? "MeV" : unit === "nt" ? "nT" : unit}`;
    if (!measurements.some((item) => item.value === value && item.label === label)) measurements.push({ value, label });
    if (measurements.length === 4) break;
  }
  return measurements;
}

function initialStart() {
  const date = new Date();
  // The API limit is 30 calendar dates inclusive (a 29-day date difference).
  date.setUTCDate(date.getUTCDate() - 29);
  return date.toISOString().slice(0, 10);
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

export function SpaceWeatherPage() {
  const [selectedType, setSelectedType] = useState("");
  const [startDate, setStartDate] = useState(initialStart());
  const [endDate, setEndDate] = useState(today());
  const [filters, setFilters] = useState({ type: "", start_date: initialStart(), end_date: today() });
  const [page, setPage] = useState(1);
  const path = `/api/v1/space-weather/events${encodeQuery({ type: filters.type || undefined, start_date: filters.start_date, end_date: filters.end_date, page, page_size: 100 })}`;
  const resource = useApiQuery<PageResult<SpaceWeatherEvent> | SpaceWeatherEvent[]>(path);
  const events = resource.data ? toPage(resource.data).items : [];
  const days = Math.ceil((new Date(`${endDate}T00:00:00Z`).getTime() - new Date(`${startDate}T00:00:00Z`).getTime()) / 86_400_000) + 1;
  const rangeTooLong = days > 30;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (startDate > endDate || rangeTooLong) return;
    setFilters({ type: selectedType, start_date: startDate, end_date: endDate });
    setPage(1);
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="EXPLORE / SPACE WEATHER" title="Space-weather monitor" description="Browse NASA DONKI event records by event class and UTC date range." actions={<span className="source-pill"><Activity size={13} /> DONKI</span>} />
      <section className="panel filter-panel">
        <form className="filter-form weather-filters" onSubmit={submit}>
          <label className="field-label" htmlFor="donki-type">Event type
            <select id="donki-type" value={selectedType} onChange={(event) => setSelectedType(event.target.value)}><option value="">Notifications feed (multiple event types)</option>{EVENT_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}</select>
          </label>
          <label className="field-label" htmlFor="donki-start">Start date <span className="optional-note">UTC</span><input id="donki-start" type="date" value={startDate} max={today()} required onChange={(event) => setStartDate(event.target.value)} /></label>
          <label className="field-label" htmlFor="donki-end">End date <span className="optional-note">UTC</span><input id="donki-end" type="date" value={endDate} max={today()} required onChange={(event) => setEndDate(event.target.value)} /></label>
          <button className="button button-primary" type="submit" disabled={startDate > endDate || rangeTooLong}><CalendarRange size={15} /> Apply window</button>
        </form>
        {startDate > endDate && <p className="field-error" role="alert">Start date must be on or before end date.</p>}
        {rangeTooLong && <p className="field-error" role="alert">DONKI supports a maximum 30-calendar-day window. Shorten the selected range before applying it.</p>}
      </section>

      <section className="panel events-panel" aria-labelledby="weather-results-heading">
        <SectionTitle title="Event records" detail={`${filters.start_date} — ${filters.end_date} · UTC`} />
        {resource.pending && events.length === 0 && <LoadingState label="Loading DONKI events…" />}
        {resource.error && events.length === 0 && <ErrorState error={resource.error} onRetry={resource.refresh} />}
        {!resource.pending && !resource.error && events.length === 0 && <EmptyState title="No events found in this stored time window" />}
        {resource.error && events.length > 0 && <div className="stale-notice" role="status">Refresh failed; displaying the previous event records.</div>}
        {events.length > 0 && (
          <div className="event-list">
            {events.map((event, index) => {
              const notification = event.event_type.toLowerCase() === "notifications" || Boolean(event.details?.messageBody);
              const parsed = notification ? parseNotification(event) : undefined;
              const category = parsed?.category || event.title || event.event_type;
              const { Icon, theme } = weatherVisual(category);
              const time = parsed?.issueTime || event.start_time;
              const summary = parsed?.summary || event.summary || "";
              const measurements = extractMeasurements(summary);
              return (
                <article className={`weather-event-card weather-event-${theme}`} key={`${event.event_id || event.activity_id || event.event_type}-${index}`}>
                  <div className="weather-event-marker"><Icon size={21} aria-hidden="true" /></div>
                  <div className="weather-event-content">
                    <div className="weather-event-header">
                      <span className="weather-event-kind">{notification ? "Space weather notification" : event.event_type}</span>
                      <span className="weather-event-time"><Clock3 size={13} aria-hidden="true" />{time ? formatDateTime(time) : "Time unavailable"}</span>
                    </div>
                    <h3>{category}</h3>
                    {summary && <p className="weather-event-summary">{summary}</p>}
                    {measurements.length > 0 && (
                      <div className="weather-event-indicators" aria-label="Reported measurements from the source">
                        {measurements.map((item) => <span key={`${item.value}-${item.label}`}><strong>{item.value}</strong><small>{item.label}</small></span>)}
                      </div>
                    )}
                    {notification && parsed && (parsed.messageId || parsed.activityId) && (
                      <div className="weather-event-identifiers">
                        {parsed.messageId && <span><strong>Message</strong>{parsed.messageId}</span>}
                        {parsed.activityId && <span><strong>Activity</strong>{parsed.activityId}</span>}
                      </div>
                    )}
                    {notification && parsed && (parsed.disclaimer || parsed.notes || parsed.body) && (
                      <details className="weather-event-details">
                        <summary>Read full notification and source notes</summary>
                        <div className="weather-event-detail-body">
                          {parsed.notes && <section><h4>Additional notes</h4><p>{parsed.notes}</p></section>}
                          {parsed.disclaimer && <section><h4>Source disclaimer</h4><p>{parsed.disclaimer}</p></section>}
                          <section><h4>Original message</h4><p>{parsed.body}</p></section>
                        </div>
                      </details>
                    )}
                    <div className="weather-event-footer">
                      <ProvenanceLine provenance={event.provenance} sourceUrl={event.source_url} retrievedAt={event.retrieved_at} />
                      <div className="weather-event-actions">
                        <SaveRecordButton sourceCode="DONKI" upstreamId={event.provenance?.upstream_id} />
                        {event.source_url && <a className="button button-quiet button-small" href={event.source_url} target="_blank" rel="noreferrer"><ArrowUpRight size={14} />Open source</a>}
                      </div>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
      {resource.data && <Pagination page={page} pageSize={100} total={"total" in resource.data ? resource.data.total ?? events.length : events.length} onPageChange={setPage} />}
      <div className="scientific-note panel-note">Event counts are records returned from the application store, not a severity index or forecast.</div>
    </div>
  );
}
