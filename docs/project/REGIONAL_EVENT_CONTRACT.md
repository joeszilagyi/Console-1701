# REGIONAL Event Contract (Current Fixture Slice)

REGIONAL uses the existing `news_clusters` table as a scoped event record; no separate
`regional_events` table is required for this slice. Item and cluster evidence remain JSON-heavy
and are visible through the existing scope/item APIs and evidence drawers.

## Identity And Matching

| Parser evidence | Event type | Stable identity | Geography basis |
| --- | --- | --- | --- |
| USGS earthquake | `earthquake` | official USGS event ID | point coordinates and configured bounding filter |
| NWS alert | `weather_alert` | official NWS alert ID | Washington zone IDs and area description |
| WSDOT alert | `traveler_alert` | official WSDOT alert ID | route, facility, county, and region |
| Unverified headline | `regional_headline` | source plus canonical URL hash | headline service area, not trusted for convergence |

The persisted event key is a stable hash of the corresponding identity. This matches updates or
duplicate feed paths carrying the same official ID. It intentionally does not merge headlines merely
because titles or places look similar. REGIONAL NWS fixture parsing excludes alerts without
Washington zone evidence or an explicit Washington area description; the disabled registry seed
uses NWS's documented `area=WA` endpoint.

## Item And Cluster Evidence

Every newly ingested REGIONAL item records its event key/type, matching basis and tokens, confidence,
geography basis, public-impact basis, privacy basis, source family/class, parser, verification state,
fetch run, policy, retention, and ranking factors. Clusters record member item IDs, source keys,
distinct families, duplicate-family counts, corroboration state, and score. Raw article bodies are
not stored.

REGIONAL ranking keeps shared recency/priority/health factors, then adds explicit geography,
public-impact, confidence, privacy, source-diversity, cluster-size, and same-family duplicate factors.
The cluster adjustment is recalculated from base evidence on every rebuild, so repeated scans do
not accumulate a bonus. Two items from the same family increase event size but do not count as
independent corroboration. Current source health uses the shared state model; REGIONAL route tests
cover stale, parser-failed, policy-blocked, never-run, disabled, and manual-review states.

## Remaining Limits

This is deterministic identity matching for the three structured official fixture parsers, not the
full cross-family REGIONAL convergence model. Time-window matching, counties beyond existing source
fields, passes/ferries/ports/basins/volcanoes/AQI/public-health jurisdictions, syndicated-news
handling, and broader privacy/public-impact policy remain in `BACKLOG.md`. The REGIONAL NWS source
has an opt-in live path, but this event contract does not enable it or the news timer by default.
