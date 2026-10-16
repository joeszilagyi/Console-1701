# NATIONAL USGS GeoServe admin fixture verification

Checked 2026-10-15 against the official [GeoServe Regions endpoint documentation](https://earthquake.usgs.gov/ws/geoserve/regions.php). The documented `regions.json` point request accepts latitude, longitude, and `type=admin`; its nested `admin` FeatureCollection exposes country ISO, country name, and region. USGS says the admin polygons are based on processed GADM 2.0 data. This is an epicenter polygon lookup, not a felt-area or U.S. impact assessment.

Bounded exact GETs to `https://earthquake.usgs.gov/ws/geoserve/regions.json` returned HTTP 200 and `application/json` on 2026-10-15 (2026-10-16 UTC):

| Point | Admin result | Bytes |
| --- | --- | ---: |
| `48.5,-122.3` | `USA`, United States, Washington | 390 |
| `49.25,-122.9` | `CAN`, Canada, British Columbia | 389 |
| `31.5,-110.95` | `USA`, United States, Arizona | 388 |
| `31.2,-110.95` | `MEX`, Mexico, Sonora | 380 |
| `49.0,-123.0` | zero admin polygons, offshore/unknown | 271 |
| `18.2,-66.3` | `PRI`, Puerto Rico, Barranquitas | 389 |
| `13.45,144.75` | `GUM`, Guam, Chalan-Pago-Ordot | 389 |
| `-14.3,-170.7` | `ASM`, American Samoa, Eastern | 388 |

The reduced response fixture `tests/fixtures/news/national_usgs_geoserve_admin.json` keeps the exact observed request URL, `types`, admin count, and result properties for Washington, British Columbia, Sonora, the no-polygon point, and Puerto Rico. It omits server submission time and feature database IDs. The NATIONAL earthquake parser accepts this sidecar only with a `file://` USGS fixture. It verifies the official request URL and exact latitude/longitude against the earthquake point, then excludes a positively identified foreign admin polygon. U.S. and territory polygons remain eligible. A zero-polygon response remains geographically unknown and uses the existing coarse relevance filter.

At this fixture-verification stage, no app HTTP request to GeoServe was added. The parser stored
admin results as epicenter evidence only and never set affected state or multi-state impact from
them. The follow-up below defines the separate live request gate. State distribution of felt
reports remains unverified.

## Bounded live opt-in proposed for owner review

The follow-up branch adds a second request only when the existing NATIONAL USGS feed is explicitly
enabled for live `news-scan` **and** its source config sets `geoserve_admin_enrichment: true` with
`interval_minutes: 30` or longer. The default remains off. The app constructs only
`https://earthquake.usgs.gov/ws/geoserve/regions.json?latitude=<decimal>&longitude=<decimal>&type=admin`
from coordinates that passed the verified NATIONAL GeoJSON parser. Latitude/longitude are formatted
to six decimal places; callers cannot supply a URL. At most the first five parser-eligible events
are looked up per successful feed response. Each GeoServe GET has a five-second timeout, a 2 KiB
response cap, JSON content-type check, no redirects, and no environment proxy. The resulting
metadata request URL, point, admin count and country fields pass the same strict parser checks as
the observed fixture. A bounded direct GET with six-decimal coordinates returned HTTP 200,
`application/json`, 400 bytes, and a `USA`/Washington admin polygon on 2026-10-16 UTC.
The official [GeoServe web-services directory](https://earthquake.usgs.gov/ws/geoserve/)
lists Regions as a public endpoint; the reviewed Regions page does not state an endpoint-specific
rate limit. The five-request/30-minute cap and 429 backoff are therefore local conservative
limits, not a claimed USGS quota.

The scan persists `lookups_attempted`, `lookups_applied`, bytes and a completion/failure state.
After a GeoServe failure it stops further lookups; the base feed still ingests with its existing
coarse-geography basis. A malformed response discards all enrichment for that scan. If more than
five events qualify, later events keep coarse geography and the run records `bounded_partial`.
HTTP 429 starts a two-hour enrichment backoff recorded in fetch-run evidence; base-feed scans
continue at their configured interval without making GeoServe requests during that period.
An HTTP 304 base feed response performs no lookup. Successful point-admin evidence can exclude a
positively identified foreign-land epicenter; it cannot assert felt U.S. states, multi-state
impact, damage or an alert. The live response is not stored raw. This additional public official
request and its policy remain subject to owner review before merge. Live DYFI state distribution
is a separate open gate.

Once reviewed, an operator who has already enabled the parent NATIONAL and official-HTTP gates
can opt in on the exact source entry:

```yaml
news:
  scopes:
    NATIONAL:
      sources:
        - id: usgs_eq_geojson
          enabled: true
          interval_minutes: 30
          geoserve_admin_enrichment: true
```
