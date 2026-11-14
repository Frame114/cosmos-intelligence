import { ArrowDownUp, ArrowRight, Check, CircleAlert, GitCompareArrows, Search } from "lucide-react";
import { lazy, Suspense, useEffect, useMemo, useState, type FormEvent } from "react";
import { apiRequest, encodeQuery, toPage } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { Freshness, MetricCard, Pagination, ProvenanceLine, SaveRecordButton, SectionTitle, formatDate, numberOrDash } from "../components/DataComponents";
import { EmptyState, ErrorState, LoadingState } from "../components/StatePanel";
import { useApiQuery } from "../hooks/useApiQuery";
import type { AsteroidOrbit, AsteroidOrbitMapResponse, AsteroidRecord, CloseApproach, PageResult, Provenance } from "../types";

const AsteroidOrbit3D = lazy(() => import("../components/AsteroidOrbit3D").then((module) => ({ default: module.AsteroidOrbit3D })));

function approachesOf(record: AsteroidRecord): CloseApproach[] {
  return record.close_approaches || record.approaches || [];
}

function sizeRange(record: AsteroidRecord) {
  const min = record.estimated_diameter_km?.min ?? record.diameter_min_km;
  const max = record.estimated_diameter_km?.max ?? record.diameter_max_km;
  if (min == null && max == null) return "Estimate unavailable";
  return `${numberOrDash(min, 3)}–${numberOrDash(max, 3)} km`;
}

function diameterEstimateKm(record: AsteroidRecord) {
  const min = record.estimated_diameter_km?.min ?? record.diameter_min_km;
  const max = record.estimated_diameter_km?.max ?? record.diameter_max_km;
  const values = [min, max].filter((value): value is number => typeof value === "number" && Number.isFinite(value) && value > 0);
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : undefined;
}

function AsteroidDetails({ record, onClose }: { record: AsteroidRecord; onClose: () => void }) {
  const approach = approachesOf(record);
  const orbitDetails = useApiQuery<AsteroidOrbit>(`/api/v1/asteroids/${encodeURIComponent(record.neo_id)}/orbit`);
  return (
    <aside className="panel detail-panel" aria-labelledby="asteroid-detail-title">
      <div className="panel-heading"><div><p className="eyebrow">OBJECT DETAILS</p><h2 id="asteroid-detail-title">{record.name}</h2></div><button className="button button-quiet button-small" onClick={onClose} type="button">Close</button></div>
      <div className="detail-id">NeoWs object ID <code>{record.neo_id}</code></div>
      <div className="detail-metrics">
        <div><span>Estimated diameter</span><strong>{sizeRange(record)}</strong></div>
        <div><span>Absolute magnitude</span><strong>{numberOrDash(record.absolute_magnitude)}</strong></div>
      </div>
      <div className={`classification ${record.potentially_hazardous ? "classification-amber" : ""}`}>
        <CircleAlert size={17} aria-hidden="true" />
        <div><strong>NASA potentially hazardous classification</strong><span>{record.potentially_hazardous === null || record.potentially_hazardous === undefined ? "Not supplied by source" : record.potentially_hazardous ? "Flagged by the upstream classification" : "Not flagged by the upstream classification"}</span></div>
      </div>
      <p className="scientific-note">This source classification is not an impact probability or an independent risk prediction.</p>
      <SectionTitle title="JPL orbital solution" detail="Current SBDB orbital elements and physical data." />
      {orbitDetails.pending && <p className="detail-loading-copy">Loading JPL solution…</p>}
      {orbitDetails.error && <div className="detail-loading-copy">{orbitDetails.error.message} <button className="button button-quiet button-small" type="button" onClick={orbitDetails.refresh}>Retry</button></div>}
      {orbitDetails.data && <div className="detail-orbital-grid">{orbitDetails.data.orbital_elements.filter((item) => ["e", "a", "q", "i", "moid"].includes((item.name || "").toLowerCase())).map((item) => <div key={item.name}><small>{item.title || item.name}</small><strong>{item.value ?? "—"}{item.units ? ` ${item.units}` : ""}</strong></div>)}{orbitDetails.data.physical_parameters.filter((item) => item.value && ["diameter", "rot_per", "albedo"].includes((item.name || "").toLowerCase())).slice(0, 3).map((item) => <div key={`physical-${item.name}`}><small>{item.title || item.name}</small><strong>{item.value}{item.units ? ` ${item.units}` : ""}</strong></div>)}</div>}
      <SectionTitle title="Close approaches" detail="Values remain in their source-provided units." />
      {approach.length === 0 ? <EmptyState title="No approach records in this response" /> : (
        <div className="approach-list">
          {approach.map((item, index) => (
            <div className="approach-row" key={`${item.date || item.close_approach_date || "unknown"}-${index}`}>
              <span className="approach-date">{formatDate(item.date || item.close_approach_date)}</span>
              <span><small>Relative velocity</small><strong>{numberOrDash(item.relative_velocity_km_s ?? item.velocity_km_s)} km/s</strong></span>
              <span><small>Miss distance</small><strong>{numberOrDash(item.miss_distance_km)} km</strong></span>
            </div>
          ))}
        </div>
      )}
      <ProvenanceLine provenance={record.provenance} retrievedAt={record.retrieved_at} />
      <SaveRecordButton sourceCode="NEOWS" upstreamId={record.neo_id} />
    </aside>
  );
}

export function AsteroidsPage() {
  const [query, setQuery] = useState("");
  const [hazardous, setHazardous] = useState("");
  const [minimumDiameter, setMinimumDiameter] = useState("");
  const [maximumDiameter, setMaximumDiameter] = useState("");
  const [applied, setApplied] = useState({ q: "", hazardous: "", minimumDiameter: "", maximumDiameter: "" });
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<AsteroidRecord | null>(null);
  const [orbitMap, setOrbitMap] = useState<AsteroidOrbitMapResponse>();
  const [orbitMapPending, setOrbitMapPending] = useState(false);
  const [orbitMapError, setOrbitMapError] = useState<Error | null>(null);
  const [orbitMapRevision, setOrbitMapRevision] = useState(0);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<unknown>(null);
  const [compareError, setCompareError] = useState<string | null>(null);
  const listPath = `/api/v1/asteroids${encodeQuery({ q: applied.q, potentially_hazardous: applied.hazardous || undefined, minimum_diameter_km: applied.minimumDiameter, maximum_diameter_km: applied.maximumDiameter, page, page_size: 50 })}`;
  const resource = useApiQuery<PageResult<AsteroidRecord> | AsteroidRecord[]>(listPath);
  const records = resource.data ? toPage(resource.data).items : [];
  const orbitMapRequest = useMemo(() => JSON.stringify({ objects: records.map((record) => ({
    neo_id: record.neo_id,
    name: record.name,
    diameter_km: diameterEstimateKm(record),
    potentially_hazardous: record.potentially_hazardous,
  })) }), [records]);

  useEffect(() => {
    if (!records.length) {
      setOrbitMap(undefined);
      setOrbitMapPending(false);
      return;
    }
    const controller = new AbortController();
    setOrbitMap(undefined);
    setOrbitMapError(null);
    setOrbitMapPending(true);
    void apiRequest<AsteroidOrbitMapResponse>("/api/v1/asteroids/orbit-map", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: orbitMapRequest,
      signal: controller.signal,
    }).then((data) => {
      if (!controller.signal.aborted) setOrbitMap(data);
    }).catch((error: unknown) => {
      if (!controller.signal.aborted) setOrbitMapError(error instanceof Error ? error : new Error("The 3D orbit map could not be loaded."));
    }).finally(() => {
      if (!controller.signal.aborted) setOrbitMapPending(false);
    });
    return () => controller.abort();
  }, [orbitMapRequest, orbitMapRevision, records.length]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (invalidDiameterRange) return;
    setApplied({ q: query.trim(), hazardous, minimumDiameter, maximumDiameter });
    setPage(1);
    setSelected(null);
    setComparison(null);
    setCompareError(null);
  }

  const invalidDiameterRange = Boolean(minimumDiameter && maximumDiameter && Number(minimumDiameter) > Number(maximumDiameter));

  function toggleCompare(id: string) {
    setCompareIds((current) => current.includes(id) ? current.filter((value) => value !== id) : current.length < 10 ? [...current, id] : current);
  }

  async function compareSelected() {
    setCompareError(null);
    try {
      const result = await apiRequest<unknown>("/api/v1/asteroids/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ neo_ids: compareIds }),
      });
      setComparison(result);
    } catch (error) {
      setCompareError(error instanceof Error ? error.message : "The comparison could not be loaded.");
    }
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="EXPLORE / NEAR-EARTH OBJECTS" title="Asteroid intelligence" description="Inspect recorded approach data and source classifications. Measurements are shown with their original units." />
      <section className="panel filter-panel">
        <form className="filter-form asteroid-filters" onSubmit={submit}>
          <label className="field-label field-search-label" htmlFor="neo-search">Search by name or object ID
            <span className="input-with-icon"><Search size={15} aria-hidden="true" /><input id="neo-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} maxLength={100} placeholder="Search stored objects…" /></span>
          </label>
          <label className="field-label" htmlFor="hazard-filter">Source classification
            <select id="hazard-filter" value={hazardous} onChange={(event) => setHazardous(event.target.value)}><option value="">All classifications</option><option value="true">Potentially hazardous</option><option value="false">Not flagged</option></select>
          </label>
          <label className="field-label" htmlFor="diameter-min">Minimum diameter (km)<input id="diameter-min" type="number" min="0" step="any" value={minimumDiameter} onChange={(event) => setMinimumDiameter(event.target.value)} /></label>
          <label className="field-label" htmlFor="diameter-max">Maximum diameter (km)<input id="diameter-max" type="number" min="0" step="any" value={maximumDiameter} onChange={(event) => setMaximumDiameter(event.target.value)} /></label>
          <button className="button button-primary" type="submit" disabled={invalidDiameterRange}>Apply filters <ArrowDownUp size={15} /></button>
        </form>
        {invalidDiameterRange && <p className="field-error" role="alert">Minimum diameter must not be greater than maximum diameter.</p>}
        {(minimumDiameter || maximumDiameter) && <p className="helper-copy">Diameter filters keep objects whose source estimate overlaps the requested range. Objects without enough diameter data are omitted.</p>}
      </section>

      <div className="metric-grid metric-grid-three">
        <MetricCard label="Stored records" value={resource.data ? toPage(resource.data).total ?? records.length : "—"} detail="Records in application storage" icon={<GitCompareArrows size={17} />} />
        <MetricCard label="Selected to compare" value={`${compareIds.length} / 10`} detail="Choose at least two objects" icon={<Check size={17} />} tone="cyan" />
        <MetricCard label="Date coverage" value="Source dependent" detail="Approach history depends on ingested windows" icon={<ArrowDownUp size={17} />} tone="amber" />
      </div>

      {records.length > 0 && orbitMap && <Suspense fallback={<section className="panel asteroid-3d-loading"><p>Loading interactive 3D viewer…</p></section>}><AsteroidOrbit3D data={orbitMap} selectedId={selected?.neo_id ?? orbitMap.objects[0]?.neo_id} onSelect={(neoId) => { const record = records.find((item) => item.neo_id === neoId); if (record) setSelected(record); }} /></Suspense>}
      {records.length > 0 && !orbitMap && <section className="panel asteroid-3d-loading" aria-live="polite"><div className="asteroid-loading-orbit"><span /></div><div><p className="eyebrow">JPL HORIZONS · 3D EPHEMERIS</p><h2>Building the Earth-centered map</h2><p>{orbitMapPending ? `Calculating shared six-hour trajectories for ${records.length} asteroids…` : orbitMapError?.message ?? "Preparing a common time window for the current catalogue page."}</p>{orbitMapError && <button type="button" className="button button-quiet button-small" onClick={() => setOrbitMapRevision((revision) => revision + 1)}>Retry trajectory load</button>}</div></section>}

      {resource.pending && records.length === 0 && <LoadingState label="Loading near-Earth object records…" />}
      {resource.error && records.length === 0 && <ErrorState error={resource.error} onRetry={resource.refresh} />}
      {records.length === 0 && !resource.pending && !resource.error && <EmptyState title="No asteroid records match these filters" />}

      {records.length > 0 && (
        <div className="asteroid-layout">
          <section className="panel table-panel" aria-labelledby="asteroid-results-title">
            <SectionTitle title="Object catalogue" detail={`${records.length} record${records.length === 1 ? "" : "s"} returned`} />
            <div className="table-scroll">
              <table className="data-table">
                <thead><tr><th scope="col"><span className="sr-only">Compare</span></th><th scope="col">Object</th><th scope="col">Diameter estimate</th><th scope="col">Source flag</th><th scope="col">Approaches</th><th scope="col"><span className="sr-only">Details</span></th></tr></thead>
                <tbody>
                  {records.map((record) => (
                    <tr key={record.neo_id} className={selected?.neo_id === record.neo_id ? "selected-row" : ""}>
                      <td><input aria-label={`Add ${record.name} to comparison`} type="checkbox" checked={compareIds.includes(record.neo_id)} onChange={() => toggleCompare(record.neo_id)} /></td>
                      <td><button type="button" className="table-primary-button" onClick={() => setSelected(record)}><strong>{record.name}</strong><small>{record.neo_id}</small></button></td>
                      <td className="numeric-cell">{sizeRange(record)}</td>
                      <td><span className={`table-flag ${record.potentially_hazardous ? "table-flag-warning" : ""}`}>{record.potentially_hazardous == null ? "Not supplied" : record.potentially_hazardous ? "Flagged" : "Not flagged"}</span></td>
                      <td className="numeric-cell">{approachesOf(record).length || "—"}</td>
                      <td><button className="icon-button table-open-button" aria-label={`Open details for ${record.name}`} onClick={() => setSelected(record)} type="button"><ArrowRight size={16} /></button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="table-footer"><span>Source classifications are presented without additional risk interpretation.</span><span>{(resource.data as PageResult<AsteroidRecord> | undefined)?.freshness && <Freshness value={(resource.data as PageResult<AsteroidRecord>).freshness} />}</span></div>
            {resource.error && <div className="stale-inline">Refresh failed; showing the previous result.</div>}
          </section>

          {selected && <AsteroidDetails record={selected} onClose={() => setSelected(null)} />}
        </div>
      )}

      {resource.data && <Pagination page={page} pageSize={50} total={"total" in resource.data ? resource.data.total ?? records.length : records.length} onPageChange={setPage} />}

      <div className="comparison-row">
        <div><strong>Compare selected objects</strong><span>Select 2–10 objects. Missing measurements stay blank; units are shown explicitly.</span></div>
        <button className="button button-secondary" type="button" onClick={compareSelected} disabled={compareIds.length < 2}>Compare {compareIds.length ? `(${compareIds.length})` : "objects"} <ArrowRight size={14} /></button>
      </div>
      {compareError && <div className="state-panel state-error" role="alert"><CircleAlert size={17} /><span>{compareError}</span></div>}
      {comparison !== null && <ComparisonResult value={comparison} />}
    </div>
  );
}

function ComparisonResult({ value }: { value: unknown }) {
  const result = value as {
    objects?: Array<{
      neo_id: string;
      name: string;
      absolute_magnitude?: number | null;
      potentially_hazardous?: boolean | null;
      estimated_diameter_km?: { min?: number | null; max?: number | null };
      close_approaches?: CloseApproach[];
    }>;
    units?: { diameter?: string; relative_velocity?: string; miss_distance?: string };
    disclaimer?: string;
  };
  return (
    <section className="panel comparison-result">
      <SectionTitle title="Object comparison" detail={`Diameter: ${result.units?.diameter || "km"} · approach speed: ${result.units?.relative_velocity || "km/s"} · miss distance: ${result.units?.miss_distance || "km"}`} />
      <div className="table-scroll"><table className="data-table"><thead><tr><th>Object</th><th>Diameter estimate</th><th>Absolute magnitude</th><th>NASA source flag</th><th>Next approach</th><th>Velocity</th><th>Miss distance</th></tr></thead><tbody>
        {result.objects?.map((object) => {
          const approach = [...(object.close_approaches || [])].sort((a, b) => (a.date || "").localeCompare(b.date || ""))[0];
          const min = object.estimated_diameter_km?.min;
          const max = object.estimated_diameter_km?.max;
          const diameter = min == null && max == null ? "—" : `${numberOrDash(min, 3)}–${numberOrDash(max, 3)} km`;
          const hazardous = object.potentially_hazardous == null ? "Not supplied" : object.potentially_hazardous ? "Flagged" : "Not flagged";
          return <tr key={object.neo_id}><td><strong>{object.name}</strong><small>{object.neo_id}</small></td><td>{diameter}</td><td>{numberOrDash(object.absolute_magnitude)}</td><td>{hazardous}</td><td>{formatDate(approach?.date)}</td><td>{numberOrDash(approach?.relative_velocity_km_s)} km/s</td><td>{numberOrDash(approach?.miss_distance_km)} km</td></tr>;
        })}
      </tbody></table></div>
      <p className="scientific-note">{result.disclaimer || "Measurements are descriptive and are not an impact prediction."}</p>
    </section>
  );
}

export type { Provenance };
