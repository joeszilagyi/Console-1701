# GDACS and USGS earthquake origin correlation

Verified 2026-10-15 for RS-078 against the existing reduced observed
[GDACS GeoJSON fixture](../../tests/fixtures/news/global_gdacs.geojson) and a bounded GET of
the official [USGS M4.5+ past-week GeoJSON feed](https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson).
The USGS read returned HTTP 200, 120,403 bytes, and 172 features. A reduced observed USGS
feature is stored in `tests/fixtures/news/global_usgs_gdacs_costa_rica.json`.

GDACS EQ 1571782 and USGS `us6000u2i9` both report an M4.5 Costa Rica earthquake at
longitude -86.049 and latitude 10.3031. GDACS `fromdate` is 2026-10-15 15:40:38 UTC;
the USGS origin is 15:40:38.840 UTC. The GDACS and USGS URLs and identifiers remain
separate. The matcher joins only official GDACS EQ and USGS earthquake rows with valid
source-family evidence, origin times within five seconds, epicenters within two kilometers,
and magnitudes within 0.1. It uses the measured origin fields, not place labels or broad
headline tokens. Changed time, location, magnitude, status or family do not match; a
complete-link regression prevents one GDACS row from bridging two distinct USGS events.

[GDACS's earthquake model description](https://data.gdacs.org/Knowledge/models_eq.aspx)
states that its earthquake calculations incorporate seismic parameters and, when available,
USGS ShakeMaps. An origin match therefore represents a shared underlying earthquake, not
independent observational confirmation. The group keeps both source families for provenance,
but credits only USGS for family-diversity and cluster-size factors in this paired case.
GDACS's separately computed alert level can still contribute severity. The stored event
explicitly remains `corroborated: false` with no invented affected-country or impact claim.

The offline `news-scan` test uses a local GDACS fixture and a local USGS fixture with the
GLOBAL magnitude threshold explicitly set to 4.5. It traps HTTP and verifies one stored
two-item event, one credited source family, and one credited cluster item. The normal GLOBAL
threshold remains 6.0; this fixture does not enable either source for live ingest.
