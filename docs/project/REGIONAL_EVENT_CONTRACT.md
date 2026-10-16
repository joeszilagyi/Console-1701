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
| WSF bulletin | `ferry_alert` | official bulletin ID | affected route IDs; all-routes flag stays distinct |
| USGS water observation | `hydrology_observation` | official gauge ID and observation time | station county and HUC8 basin |
| Ecology AQI observation | `air_quality_observation` | official site ID and sample time | allowlisted station and city |
| Pierce County road alert | `traveler_alert` | official AID | publisher jurisdiction, Pierce County |
| Unverified headline | `regional_headline` | source plus canonical URL hash | headline service area, not trusted for convergence |

The persisted event key is a stable hash of the corresponding identity. This matches updates or
duplicate feed paths carrying the same official ID. The cluster rebuild can also correlate two
different official source families when event type, one verified geographic field, at least three
normalized title tokens, and publication times within 48 hours all agree. Current parser-backed
geographic fields include WSDOT route/county, NWS weather zone, Pierce County jurisdiction,
WSF route IDs, USGS water basin/county, and Ecology station/city. Event type still has to match;
the Pierce and WSDOT road reports can converge on a shared county and title. County comparison
normalizes an optional terminal `County` suffix (for example, `Pierce` and `Pierce County`)
without treating distinct counties as the same place. A two-parser offline scan persists this
cross-family match and a different-county negative case. The WSDOT record in that regression
uses the documented synthetic API shape; it is not an observed authenticated response.
Future official parsers can supply the other named REGIONAL identity fields. Every pair in a multi-item group must
match; a general middle report cannot bridge two unrelated incidents. Unverified headlines remain
isolated even when their title and place resemble an official report. REGIONAL NWS fixture parsing excludes alerts without
Washington zone evidence or an explicit Washington area description; the disabled registry seed
uses NWS's documented `area=WA` endpoint.

## Item And Cluster Evidence

Every newly ingested REGIONAL item records its event key/type, matching basis and tokens, confidence,
geography basis, public-impact basis, privacy basis, source family/class, parser, verification state,
fetch run, policy, retention, and ranking factors. Clusters record member item IDs, source keys,
distinct families, duplicate-family counts, corroboration state, and score. Raw article bodies are
not stored. The versioned `regional` item contract gathers source identity and official status,
URLs, publication and observation times, health, geography, matching, public impact, privacy
redaction, ranking, retention, and policy notes. Cluster evidence includes a snapshot of this
contract for each member and pairwise match reasons; the REGIONAL page item and cluster drawers
show those decisions.

REGIONAL ranking keeps shared recency/priority/health factors, then adds explicit geography,
public-impact, confidence, privacy, source-diversity, cluster-size, and same-family duplicate factors.
An active NWS alert receives an expiry-bounded bonus; a stale source and rejected seismic geography
receive explicit penalties. Corroborated reports receive a bounded publication-time proximity bonus
when all member timestamps are present. These factors and reasons are stored on each item.
The cluster adjustment is recalculated from base evidence on every rebuild, so repeated scans do
not accumulate a bonus. Two items from the same family increase event size but do not count as
independent corroboration. Current source health uses the shared state model; REGIONAL route tests
cover stale, parser-failed, policy-blocked, never-run, disabled, and manual-review states.

## Remaining Limits

This is deterministic identity matching for the structured official fixture parsers, plus a
conservative cross-family path for their verified geography. Additional county and incident
sources, passes, airports, ports, volcanoes, public-health jurisdictions, and syndicated-news
handling remain in `BACKLOG.md`. REGIONAL NWS and USGS
have opt-in live paths, but this event contract does not enable them or the news timer by default.
