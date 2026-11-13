# MCP Tools

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Phase 1 tool catalog; confirm SDK schema syntax at implementation  
**Purpose:** Specify the intended MCP Tools requirements and implementation constraints.  
**Scope:** Covers the proposed MCP Tools behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



All tools return JSON objects with a provenance array where a source record is returned. All list outputs are capped to 50 records. The report tool is disabled until its AI-policy gate is resolved.

## 1. search_astronomy_records

**Description:** Search APOD records by text/date and return normalized metadata.  
**Input:** query string? (1–200 chars), start_date/end_date ISO date?, media_type enum image|video|iframe?, page integer default 1, page_size 1–50 default 20. Reject inverted ranges and ranges over 366 days unless operator backfill is used.  
**Output:** items[] of {date,title,media_type,explanation_excerpt,alt,credit,record_id,source_url,retrieved_at}, page, page_size, total.  
**Validation/permission:** Public-read data scope; plain text only; output strips HTML.  
**Service:** AstronomySearchService.  
**Example input:** {"query":"galaxy","start_date":"2026-01-01","end_date":"2026-01-31","media_type":"image","page":1,"page_size":10}  
**Example result shape:** {"items":[{"date":"2026-01-02","title":"...","media_type":"image","record_id":"...","source_url":"https://science.nasa.gov/...","retrieved_at":"2026-01-03T00:00:00Z"}],"page":1,"page_size":10,"total":1}

## 2. get_astronomy_picture

**Description:** Retrieve one APOD Basic record by date.  
**Input:** date ISO date.  
**Output:** date,title,media_type,explanation,media_url?,page_url,alt?,credit?,copyright?,record_id,retrieved_at.  
**Validation/permission:** Valid date; public-read. Return not-found if no source item exists.  
**Service:** AstronomyRecordService.  
**Example input:** {"date":"2026-11-12"}  
**Example result shape:** {"date":"2026-11-12","title":"...","media_type":"image","page_url":"https://science.nasa.gov/...","record_id":"...","retrieved_at":"2026-11-13T00:00:00Z"}

## 3. search_asteroids

**Description:** Search cached NeoWs objects and close approaches.  
**Input:** query string?, start_date/end_date?, potentially_hazardous boolean?, minimum_diameter_km/maximum_diameter_km?, page default 1, page_size 1–50. Date window maximum seven days for feed-backed refresh; wider search uses locally stored history and reports coverage.  
**Output:** items[] of {neo_id,name,absolute_magnitude?,diameter_min_km?,diameter_max_km?,potentially_hazardous?,approaches[],record_id,source_url,retrieved_at}, page metadata.  
**Validation/permission:** Public-read; non-negative diameter; no impact-risk language.  
**Service:** NeoSearchService.  
**Example input:** {"start_date":"2026-11-12","end_date":"2026-11-13","potentially_hazardous":true,"page":1,"page_size":10}  
**Example result shape:** {"items":[{"neo_id":"3542519","name":"...","potentially_hazardous":true,"approaches":[{"date":"2026-11-13","velocity_km_s":null,"miss_distance_km":null}],"record_id":"...","retrieved_at":"..."}],"page":1,"page_size":10,"total":1}

## 4. get_asteroid_details

**Description:** Retrieve one NeoWs object and its approaches.  
**Input:** neo_id string matching 1–20 digits, start_date/end_date optional.  
**Output:** normalized object fields, approaches with units, upstream hazardous/sentry flags, provenance.  
**Validation/permission:** Public-read; verify ID against numeric pattern before query.  
**Service:** NeoDetailsService.  
**Example input:** {"neo_id":"3542519"}  
**Example result shape:** {"neo_id":"3542519","name":"...","potentially_hazardous":false,"diameter_km":{"min":null,"max":null},"approaches":[],"provenance":{"source":"NEOWS","record_id":"...","retrieved_at":"..."}}

## 5. compare_asteroids

**Description:** Compare 2–10 objects on explicitly aligned fields and approach window.  
**Input:** neo_ids unique array length 2–10, approach_start/end optional ISO dates.  
**Output:** objects[], comparison_fields[] with names/units/values, missing_fields[], window, provenance[].  
**Validation/permission:** Authenticated read scope; maximum 10 IDs; only numeric IDs; no computed impact score.  
**Service:** NeoComparisonService.  
**Example input:** {"neo_ids":["3542519","2000433"],"approach_start":"2026-01-01","approach_end":"2026-12-31"}  
**Example result shape:** {"objects":[{"neo_id":"3542519","name":"..."}],"comparison_fields":[{"field":"diameter_max_km","unit":"km","values":{"3542519":null,"2000433":0.4}}],"missing_fields":["diameter_max_km:3542519"],"provenance":[]}

## 6. search_space_weather_events

**Description:** Search DONKI event records by supported type and UTC date window.  
**Input:** event_types enum array from CME,CMEAnalysis,GST,IPS,FLR,SEP,MPC,RBE,HSS,WSAEnlilSimulations,notifications; start_date/end_date required, maximum 30 days; page/page_size.  
**Output:** items[] {event_type,event_id,start_time?,title?,summary?,source_url,record_id,retrieved_at}.  
**Validation/permission:** Public-read; supported type only; range <=30 days.  
**Service:** SpaceWeatherSearchService.  
**Example input:** {"event_types":["FLR","GST"],"start_date":"2026-11-01","end_date":"2026-11-13","page_size":20}  
**Example result shape:** {"items":[{"event_type":"FLR","event_id":"...","start_time":"...","source_url":"https://api.nasa.gov/DONKI/FLR","record_id":"...","retrieved_at":"..."}],"page":1,"page_size":20,"total":1}

## 7. get_space_weather_summary

**Description:** Return a record-count summary by DONKI type over a date range.  
**Input:** start_date/end_date ISO dates, maximum 30 days; event_types optional enum array.  
**Output:** window UTC, counts_by_type, latest_retrieved_at, provenance records or source windows.  
**Validation/permission:** Public-read; a summary is a record count, not a space-weather severity index.  
**Service:** SpaceWeatherSummaryService.  
**Example input:** {"start_date":"2026-11-01","end_date":"2026-11-13"}  
**Example result shape:** {"window":{"start":"2026-11-01","end":"2026-11-13","timezone":"UTC"},"counts_by_type":{"FLR":0,"GST":0},"provenance":[]}

## 8. search_earth_events

**Description:** Search EONET v3 curated event metadata.  
**Input:** categories string array?, status open|closed|all default open, start/end?, bbox [min_lon,max_lat,max_lon,min_lat]?, page_size 1–50 default 20.  
**Output:** items[] {event_id,title,description?,status,opened_at?,closed_at?,categories[],geometry?,sources[],source_url}, pagination where local results support it.  
**Validation/permission:** Public-read; bbox numeric bounds checked; category IDs validated from current category catalog.  
**Service:** EarthEventSearchService.  
**Example input:** {"categories":["wildfires"],"status":"open","page_size":20}  
**Example result shape:** {"items":[{"event_id":"EONET_...","title":"...","status":"open","categories":["wildfires"],"geometry":null,"sources":[],"source_url":"https://eonet.gsfc.nasa.gov/..."}],"total":1}

## 9. search_nasa_media

**Description:** Search NASA Image and Video Library metadata and asset links.  
**Input:** query string 1–200 chars or nasa_id, media_type image|video|audio, year_start/year_end?, page default 1, page_size 1–50 default 20.  
**Output:** items[] {nasa_id,title,media_type,date_created?,description?,creators[],thumbnail_url?,detail_url,asset_manifest_url,rights_note?}, pagination.  
**Validation/permission:** Public-read; HTTPS NASA host allowlist for returned links; no server fetch of arbitrary asset URL.  
**Service:** NasaMediaSearchService.  
**Example input:** {"query":"nebula","media_type":"image","year_start":"2020","year_end":"2025","page_size":10}  
**Example result shape:** {"items":[{"nasa_id":"...","title":"...","media_type":"image","detail_url":"https://images.nasa.gov/details/...","asset_manifest_url":"https://images-api.nasa.gov/asset/..."}],"page":1,"page_size":10,"total":1}

## 10. generate_scientific_report

**Description:** Create a bounded, cited report from validated application records. Disabled until NASA policy review and AI release gate pass.  
**Input:** question 1–4000 chars, domains enum array, date range?, format summary|comparison|brief default summary, max_records 1–12 default 8.  
**Output:** report_id,status,generated_by,answer,observed_facts[],interpretation[],limitations[],citations[],prompt_version,model_id,generated_at.  
**Validation/permission:** Authenticated research:generate scope; 3 reports/hour/subject plus provider budget; no evidence means abstain; user owns stored report.  
**Service:** ScientificReportService → retrieval + AI orchestrator.  
**Example input:** {"question":"Compare the retrieved values for these objects.","domains":["asteroids"],"format":"comparison","max_records":8}  
**Example result shape:** {"report_id":"...","status":"complete","generated_by":"Cosmos Intelligence AI","answer":"...","observed_facts":[],"interpretation":[],"limitations":["..."],"citations":[],"prompt_version":"report.v1","model_id":"configured-model","generated_at":"..."}

## Common error handling

Use stable MCP error codes for invalid input, not found, authorization, rate limit, upstream unavailable, evidence insufficient, and internal failure. Do not expose provider payloads, NASA keys, SQL, or stack traces.

## Related documents

[MCP Specification](MCP_SPECIFICATION.md), [API Specification](../02-technical/API_SPECIFICATION.md), [AI Guardrails](../04-ai-engineering/AI_GUARDRAILS.md).
