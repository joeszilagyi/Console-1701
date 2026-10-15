# Regional utility outage endpoint review

Reviewed 2026-10-15 for the deferred PSE/SnoPUD/Tacoma outage research row and RS-016.
This review establishes human reference links and an ingest decision. It does not prove that a
public API does not exist.

| Utility | Official surface reviewed | Machine-readable result and decision |
| --- | --- | --- |
| Puget Sound Energy | [Outage center](https://www.pse.com/en/outage) and its [outage map](https://www.pse.com/en/outage/outage-map) | The center links map, reporting and customer resources. No official public event RSS/API contract was established from these pages. Both registry entries stay reference-only. |
| Snohomish County PUD | [Outage center](https://www.snopud.com/outages-safety/outage-center/) and [outage map](https://outagemap.snopud.com/) | The center offers map, reporting and notifications. No official public event RSS/API contract was established. Both entries stay reference-only. |
| Tacoma Power | [Power outage page](https://www.mytpu.org/outages-safety/power-outages/) and [outage safety](https://www.mytpu.org/outages-safety/) | The pages direct readers to map/reporting and safety guidance. No official public event RSS/API contract was established. Both entries stay reference-only. |
| Seattle City Light | [View and Report Outages](https://www.citylink.seattle.gov/city-light/outages) and its map | The map says it updates every five minutes but excludes underground network areas and warns that estimates may be incomplete or delayed. No official public event RSS/API contract was established. Registry page/map entries stay reference-only. |

The three center/page entries previously labeled `static_html_headline_candidate` are now
`source_health_probe_only` in the registry and design inventory. Their HTML is not an outage-event
feed and is not parsed. A regression enables all three with nonexistent local fixture paths and
traps both fixture and HTTP access; each reports `unsupported` without reading the paths.

Do not derive customer counts, street addresses, polygons, restoration times or regional impact
from map HTML, ArcGIS Experience, account lookups or undocumented browser requests. An exact
officially published data endpoint would need a new source verification record, access/terms,
bounded shape sample, privacy/aggregation rule, stale-data policy, parser tests and controlled
`news-scan` before any live admission. Until then, RS-016 needs no invented outage fixture; this
dimension is explicitly source-blocked rather than silently omitted.
