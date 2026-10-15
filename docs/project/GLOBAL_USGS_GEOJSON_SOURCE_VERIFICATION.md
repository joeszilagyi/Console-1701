# GLOBAL USGS GeoJSON fixture contract

Verified against USGS documentation on 2026-10-15. This records a fixture parser contract; it
does not enable live HTTP ingest.

## Official references

- [USGS GeoJSON Summary Format](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)
  documents the `FeatureCollection`, event `id`, `properties`, and Point coordinates.
- [USGS M4.5+ Past Week GeoJSON feed](https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson)
  was checked for the documented shape and a current event response. This is a candidate for a
  later exact-allowlisted live phase, not an app endpoint today.
- [USGS Earthquake Catalog API documentation](https://earthquake.usgs.gov/fdsnws/event/1/)
  documents server-side magnitude, depth, felt, intensity, and time queries. The first pass uses
  local filtering of a bounded fixture rather than catalog requests.

## Parser and scope policy

The GLOBAL parser reuses the existing `usgs_earthquake_geojson` adapter with a GLOBAL-specific
filter. It preserves event ID, magnitude/type, depth, source-provided place label, origin/update
times, official event URL, felt count, CDI/MMI, alert, tsunami flag, significance, source status,
and deterministic ranking inputs. The default magnitude comes from
`global.earthquake_min_magnitude` (6.0 unless configured).

Optional local filters are `min_magnitude`, `min_depth_km`, `max_depth_km`, `min_felt`, `min_mmi`,
`tsunami_only`, `max_age_hours`, `country_terms`, and `region_terms`. The term filters match whole
phrases in USGS's source-provided `place` text. That text is not a structured country code, so
evidence marks it `source_place_unverified` and does not manufacture affected-country labels or
cross-family geographic corroboration. Missing MMI fails a positive `min_mmi` threshold. A
positive `max_age_hours` compares origin time with the current scan time; the default is unset
so a checked-in fixture remains reproducible.

The fixture in `tests/fixtures/news/global_usgs_earthquakes.json` is synthetic but conforms to the
documented field shape. It includes high-magnitude Fiji, Iceland, and Japan earthquakes plus
below-threshold, deep, and non-earthquake rows for filter coverage. Tests prove fixture-only scan
persistence, event identity, ranking evidence, and no app HTTP request. Live use remains disabled
pending the separate official-source allowlist and operational policy phase.
