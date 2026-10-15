# OpenFEMA Disaster Declarations Research

Reviewed 2026-10-15 for RS-038. Decision: **documented public API suitable for a future
fixture parser; no NATIONAL live ingest enabled**.

## Ownership, access and bounded observation

FEMA owns [Disaster Declarations Summaries v2](https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2)
and documents `https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries` as its JSON API.
The [OpenFEMA API guide](https://www.fema.gov/about/openfema/api) says the read-only service is
free and needs no subscription or API key. It documents `$filter`, `$select`, `$orderby`, `$skip`
and `$top`; `$top` defaults to 1,000 and has a 10,000-record maximum. The dataset page listed
update frequency `R/PT20M` and a data refresh on 2026-10-15. A future console interval of six
hours would be a conservative proposal, not a FEMA rate-limit guarantee.

Three bounded direct requests on 2026-10-15 returned JSON with `metadata` and a
`DisasterDeclarationsSummaries` array: `$top=1` to inspect fields; `$top=2` with selected fields
ordered by `lastRefresh desc`; and `$top=1` filtered to `state eq 'WA'`. The response metadata
included `rundate`, selected/filter/order parameters and an entity/version. The selected recent
records showed disaster and place codes, FEMA declaration string, state, declaration type and
date, incident type and period, region, and `lastRefresh`. These were bounded research reads,
not a controlled `news-scan` or parser test; no response snapshot was committed.

## Record shape and update semantics

The dataset covers major disaster (`DR`), emergency (`EM`) and fire management (`FM`)
declarations, including declared programs and designated areas. It also warns that older county
data and fire management history are incomplete and that raw source data can contain human
errors. Tribal declarations may appear within state data. Keep these limits visible in evidence.

The [API guide](https://www.fema.gov/about/openfema/api) explicitly says its generated `id`
does **not** persist across dataset refreshes. The dataset's
[primary-key metadata](https://www.fema.gov/api/open/v1/OpenFemaDataSetFields)
returned `disasterNumber` and `placeCode` as the two `primaryKey=true` fields for v2. Use that
pair for item identity; use `femaDeclarationString` to group county/place rows into a declaration
event. Neither a repeated place row nor a late amendment is an independent disaster.

`lastRefresh` means a record was added or changed in the OpenFEMA store, not the date of the
underlying disaster or a signal that conditions are active. Use `declarationDate` and incident
dates for display/recency and retain `lastRefresh` for incremental update evidence. A future
poller should use a bounded overlapping `lastRefresh` window, stable-key upserts and pagination
where needed; it must not download the full historical dataset every scan. FEMA's API metadata
`count` is zero by default unless requested, so zero there alone does not mean no records.

## Proposed first-pass parser and ranking contract

Store only `disasterNumber`, `placeCode`, `femaDeclarationString`, state, FEMA region,
`declarationType`, `declarationDate`, `incidentType`, bounded `declarationTitle`, incident
start/end, selected declared-assistance flags, designated area, and `lastRefresh`. Treat state and
region as official labels; do not infer an exact incident footprint from designated counties or
turn tribal records into false state-only claims. Do not store full API responses or personal
data. A future fixture should cover multiple place rows for one declaration, an amended row,
DR/EM/FM types, a tribal designation, an older historical row and an empty valid result.

Ranking should value a **recent declaration** and documented assistance/impact fields, while
distinguishing it from a current hazard alert. A newly refreshed historical row should not get a
breaking-event bonus. Coalesce place rows by declaration string before cluster-size or source
diversity scoring. NATIONAL relevance may include all states and territories; a state/FEMA-region
filter can narrow an operator view, but must not silently discard nationally important events.

## Policy, retention and health gate

The [OpenFEMA terms](https://www.fema.gov/about/openfema/terms-conditions) require dataset/version
and access-date citation, a specific FEMA non-endorsement statement, and no unauthorized agency
logo use. Before any live adapter, confirm the required text and attribution in the product UI
and source evidence. The terms also prohibit attempts to reidentify individuals in aggregated
data. No published per-minute API rate limit was identified in the reviewed API guide; use bounded
requests, a conservative interval, backoff and HTTP-error health states.

Suggested retention is seven days for recent normalized items after last observation, with
declaration identity and amendment evidence re-created from future scans; the large official
historical dataset is not a local archive target. A valid zero-result incremental query is a
healthy no-change result, while malformed JSON, missing required fields, 429 and service failures
must produce distinct parser/rate-limit/failing health. Do not infer safety from no recent
declarations. A live release requires a fixture parser, scope and ranking tests, attribution,
an exact URL/query allowlist and an explicit `news-scan` opt-in. Page loads, host scans and tests
remain offline.

The separate [FEMA declaration listings](https://www.fema.gov/disaster/declarations) and
[FEMA Web Disaster Declarations v1](https://www.fema.gov/openfema-data-page/fema-web-disaster-declarations-v1)
are reference/cross-check sources for now; this review selects v2 as the structured first-pass
candidate. No ArcGIS map or webpage scraping is proposed.
