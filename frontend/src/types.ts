export interface Provenance {
  source?: string;
  upstream_id?: string;
  record_id?: string;
  source_url?: string;
  retrieved_at?: string;
  source_updated_at?: string | null;
}

export interface PageResult<T> {
  items: T[];
  page?: number;
  page_size?: number;
  total?: number;
  retrieved_at?: string;
  freshness?: "current" | "stale" | "unknown";
}

export interface ApodRecord {
  date: string;
  post_id?: number;
  title: string;
  permalink?: string;
  page_url?: string;
  media_type: "image" | "video" | "iframe" | string;
  explanation?: string;
  credit?: string | null;
  copyright?: string | null;
  alt?: string | null;
  url?: string | null;
  hdurl?: string | null;
  provenance?: Provenance;
  retrieved_at?: string;
}

export interface CloseApproach {
  date?: string;
  close_approach_date?: string;
  relative_velocity_km_s?: number | null;
  velocity_km_s?: number | null;
  miss_distance_km?: number | null;
  orbiting_body?: string | null;
}

export interface AsteroidRecord {
  neo_id: string;
  name: string;
  absolute_magnitude?: number | null;
  potentially_hazardous?: boolean | null;
  sentry_object?: boolean | null;
  estimated_diameter_km?: { min?: number | null; max?: number | null };
  diameter_min_km?: number | null;
  diameter_max_km?: number | null;
  close_approaches?: CloseApproach[];
  approaches?: CloseApproach[];
  provenance?: Provenance;
  retrieved_at?: string;
}

export interface AsteroidOrbitPoint {
  jd_tdb: number;
  date: string;
  x_au: number;
  y_au: number;
  z_au: number;
  distance_au: number;
}

export interface AsteroidOrbit {
  neo_id: string;
  name: string;
  start_date: string;
  end_date: string;
  center: string;
  reference_plane: string;
  points: AsteroidOrbitPoint[];
  orbital_elements: Array<{ name?: string; title?: string; value?: string; units?: string | null }>;
  physical_parameters: Array<{ name?: string; title?: string; value?: string; units?: string | null }>;
}

export interface AsteroidOrbitMapObject extends Pick<AsteroidRecord, "neo_id" | "name" | "potentially_hazardous"> {
  diameter_km?: number | null;
  points: AsteroidOrbitPoint[];
}

export interface AsteroidOrbitMapResponse {
  start_date: string;
  end_date: string;
  window_days: number;
  sample_interval_hours: number;
  center: string;
  reference_plane: string;
  times: Array<Pick<AsteroidOrbitPoint, "jd_tdb" | "date">>;
  objects: AsteroidOrbitMapObject[];
  unavailable: Array<{ neo_id: string; name: string }>;
}

export interface SpaceWeatherEvent {
  event_type: string;
  event_id?: string;
  activity_id?: string;
  start_time?: string | null;
  end_time?: string | null;
  title?: string;
  summary?: string;
  source_url?: string;
  details?: Record<string, unknown>;
  provenance?: Provenance;
  retrieved_at?: string;
}

export interface EonetGeometry {
  date?: string;
  type?: "Point" | "Polygon" | string;
  coordinates?: unknown;
}

export interface EarthEvent {
  event_id: string;
  id?: string;
  title: string;
  description?: string | null;
  status?: "open" | "closed" | string;
  opened_at?: string | null;
  closed_at?: string | null;
  categories?: Array<string | { id?: string; title?: string }>;
  sources?: Array<{ id?: string; url?: string; source?: string }>;
  geometry?: EonetGeometry[] | null;
  source_url?: string;
  provenance?: Provenance;
  retrieved_at?: string;
}

export interface EarthEventCoverage {
  event_id: string;
  title: string;
  description?: string | null;
  status: "open" | "closed" | string;
  categories: string[];
  observed_at?: string | null;
  eonet_url?: string | null;
  sources: Array<{ id: string; url?: string | null }>;
  satellite_imagery?: {
    service_url: string;
    name: string;
    format: "image/png" | "image/jpeg";
    date?: string | null;
    attribution: string;
  } | null;
  nasa_images: Array<{
    nasa_id: string;
    title: string;
    thumbnail_url?: string | null;
    detail_url?: string | null;
    description?: string | null;
    date_created?: string | null;
    creators?: string[];
    rights_note?: string | null;
  }>;
  related_articles: Array<{
    title: string;
    url: string;
    image_url?: string | null;
    publisher: string;
    published_at?: string | null;
    language?: string | null;
  }>;
  news_search_url?: string | null;
  retrieved_at: string;
}

export interface MediaRecord {
  nasa_id: string;
  title: string;
  media_type: "image" | "video" | "audio" | string;
  date_created?: string | null;
  description?: string | null;
  description_508?: string | null;
  keywords?: string[];
  thumbnail_url?: string | null;
  detail_url?: string | null;
  asset_manifest_url?: string | null;
  creators?: string[];
  rights_note?: string | null;
  provenance?: Provenance;
}

export interface ReportRecord {
  id: string;
  title?: string;
  question?: string;
  structured_answer?: Record<string, unknown>;
  model_id?: string;
  generated_at?: string;
  status?: string;
  citations?: Array<{ citation_key?: string; rank?: number; source?: string; upstream_id?: string; source_url?: string; retrieved_at?: string }>;
}

export interface SavedRecord {
  id: string;
  created_at: string;
  record: {
    source_code: string;
    upstream_id: string;
    title: string;
    source_url?: string | null;
    retrieved_at?: string;
    provenance?: Provenance;
  };
}

export interface ResearchConversation {
  id: string;
  title?: string | null;
  created_at: string;
  updated_at: string;
  messages?: Array<{ id: string; role: string; content: string; status: string; created_at: string }>;
}

export interface ProblemDetails {
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  code?: string;
  request_id?: string;
  retryable?: boolean;
}

export interface HealthResponse {
  status: string;
  service?: string;
  database?: string;
  version?: string;
}
