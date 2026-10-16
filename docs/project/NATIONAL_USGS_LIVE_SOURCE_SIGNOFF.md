# NATIONAL USGS GeoJSON first live source signoff

Verified 2026-10-15 for RS-055. This extends the already reviewed
[USGS M2.5+ past-day summary feed](https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson)
and the [official GeoJSON summary documentation](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)
to a separate NATIONAL scope/key allowlist. A bounded direct read returned HTTP 200,
`application/json; charset=utf-8`, 31,049 bytes, `Last-Modified`, and a `FeatureCollection`
with 43 features. The feed itself has a 2.5 magnitude floor. The NATIONAL default threshold is
5.0; live configs below 2.5 are rejected at the transport gate.

The exact allowlist entry is scope `NATIONAL`, key `usgs_eq_geojson`, URL above, kind `api_json`,
parser `usgs_earthquake_geojson`, and verification status `verified`. Every source remains disabled
by default. A live request requires `news.enabled`, `national.enabled`, the NATIONAL scope,
this source, and `news.fetch_policy.allow_official_http`, then an explicit `news-scan` command.
The transport enforces HTTPS, exact URL, bounded size/time, no inherited proxy or redirects,
conditional validators, interval, and backoff. Page loads, host scans, and pytest make no live
request. A successful zero-match response remains healthy.

The parser filters earthquake-type features by configured magnitude and coarse U.S./territory
coordinate regions. It keeps official event ID, URL, time, magnitude, felt/intensity, alert,
depth, source-place label, and filter/ranking evidence. Coordinate relevance is not a verified
state, cross-border, population, or multi-state impact determination. No raw feed body is stored.
The later first-pass country-suffix guard excludes feed events explicitly labeled in nearby
foreign countries even when their epicenters land within a coarse U.S. box. It does not infer
jurisdiction from a U.S. place label or the unlocated felt-report total.

Follow-up boundary check on 2026-10-15: the [USGS summary schema](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)
exposes a point epicenter and aggregate `felt`, `cdi`, and `mmi` fields, but no affected-state
distribution or country code. The separate [USGS GeoServe regions endpoint](https://earthquake.usgs.gov/ws/geoserve/regions.php)
can classify an individual point with an `admin` query, returning country, ISO code, and region;
it does not measure where shaking was felt. Its latitude/longitude-dependent request cannot be
added to the current exact-URL, one-feed live transport without a separately designed and
reviewed request gate. Do not convert a GeoServe epicenter classification, place label, or total
felt count into multi-state impact. Cross-border routing needs either a verified local boundary
dataset or a bounded explicit GeoServe enrichment design, and multi-state impact needs separate
source-backed geographic observations.

An isolated temporary-config/state explicit smoke scan on 2026-10-15 returned HTTP 200 and
31,049 bytes. SQLite recorded one successful fetch, `healthy` source health, one NATIONAL item
passing the 5.0 threshold and geography filter, and a `Last-Modified` validator. The temporary
opt-in and database were removed by the smoke script; standing config and timer were unchanged.
The scan's first inspection query referenced a nonexistent `response_bytes` column after the
fetch, so the isolated scan was repeated with a corrected evidence query. Only the second run's
full storage/health result is reported above. Mocked tests cover default blocking, parent/HTTP
and magnitude gates, accepted fixture ingest, interval skip, conditional 304, and scope evidence.
A live 304 and future cross-source NATIONAL correlation remain unobserved.
