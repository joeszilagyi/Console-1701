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

No app HTTP request to GeoServe was added. Live USGS scans continue using the existing single exact feed; they do not gain border certainty from this fixture-only path. The parser stores the admin result as epicenter evidence only and never sets affected state or multi-state impact from it. A live two-endpoint request design would need separate rate, query, failure, caching, and exact allowlist signoff before admission. State distribution of felt reports remains unverified.
