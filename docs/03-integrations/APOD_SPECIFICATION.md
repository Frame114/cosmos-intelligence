# APOD Basic Specification

**Version:** 1.0  
**Last updated:** 2026-11-13  
**Status:** Verified against NASA dedicated guide and a live sample; recheck on implementation.  
**Purpose:** Specify the intended APOD Basic Specification requirements and implementation constraints.  
**Scope:** Covers the proposed APOD Basic Specification behavior and interfaces; current implementation status is tracked separately.  
**Assumptions:** This is a design baseline; verify repository state and mutable upstream contracts before implementation.  



## Contract

Base URL: https://science.nasa.gov/wp-json/wp/v2/apod-basic  
Method: GET. No authentication was required by the 2026-11-13 live check. NASA’s API portal includes an api_key parameter in its summary; the dedicated APOD Basic guide does not specify that parameter. Recheck key/quota behavior before enabling it.

| Operation | Route/parameters | Result |
|---|---|---|
| Latest list | base URL with page=1&per_page=1 | JSON list of APOD records. |
| Paginated archive | base URL with page=N&per_page=N | JSON list; per_page capped at 25. Follow bounded pages. |
| Date range | date_from=YYMMDD&date_to=YYMMDD | Record(s) in the inclusive legacy-code range. |
| Single record | /YYMMDD | One APOD JSON object. |
| Raw HTML | /YYMMDD/html | Plain HTML. Do not insert into the app DOM or treat as trusted. |

The 2026-11-13 observed record keys were date, post_id, title, permalink, media_type, explanation, credit, copyright, alt, url, hdurl, basic_html, and basic_html_url. The dedicated guide also notes that fields may be absent or empty, including hdurl and explanation. Media types include image, video, and iframe.

## Portal documentation disagreement

NASA API portal summaries mention date, start_date, end_date, count (up to 25), and api_key. The current dedicated APOD Basic Feed and API User Guide documents page, per_page, date_from/date_to in YYMMDD, and /{YYMMDD}. A live date query using the portal’s date parameter returned the latest list rather than the requested date; date_from/date_to returned the requested date. Treat the dedicated guide as the working contract and add a contract test that proves date filtering before implementation acceptance.

## Domain rules and safety

- Canonical date is a date, not an assumed UTC timestamp.
- Preserve post_id as a source identifier; store the APOD permalink for attribution/navigation.
- url/permalink may point to the NASA page; do not assume it is the image binary. Use hdurl when present only after validating its scheme/host.
- Render image alt if provided. For video/iframe, display a safe outbound link unless an approved fixed-host embed allowlist and restrictive CSP are implemented.
- Do not render basic_html as executable/raw content.
- Preserve credit/copyright fields; item-level media use rights require review.

## Cache and failure policy

Application proposal: latest 6-hour cache and daily refresh; historical 24-hour cache. No service-specific quota or cache header was verified. A timeout preserves stored data with stale status; invalid payload is rejected and recorded without overwriting a previously valid normalized record.

## Example

~~~text
GET https://science.nasa.gov/wp-json/wp/v2/apod-basic?page=1&per_page=1
GET https://science.nasa.gov/wp-json/wp/v2/apod-basic?date_from=261112&date_to=261112
~~~

No example response values are reproduced here; use sanitized fixtures generated from an approved official live response after review.

## Related documents

[NASA Integrations](NASA_INTEGRATIONS.md), [API Provenance](API_PROVENANCE.md), [AI Guardrails](../04-ai-engineering/AI_GUARDRAILS.md).
