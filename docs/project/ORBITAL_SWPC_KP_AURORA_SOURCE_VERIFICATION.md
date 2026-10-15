# ORBITAL SWPC K-index and Aurora Source Verification

Checked 2026-10-15 against NOAA SWPC's public [product directory](https://services.swpc.noaa.gov/products/) and [JSON directory](https://services.swpc.noaa.gov/json/).

The designed planetary K-index summary URL at
`https://services.swpc.noaa.gov/products/summary/planetary-k-index.json` returned HTTP 404.
The registry now points to the verified
[`noaa-planetary-k-index.json`](https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json)
product: an array of `time_tag`, `Kp`, `a_running`, and `station_count` rows. The
[`planetary_k_index_1m.json`](https://services.swpc.noaa.gov/json/planetary_k_index_1m.json)
product has minute rows with `time_tag`, `kp_index`, `estimated_kp`, and `kp`; the
[`boulder_k_index_1m.json`](https://services.swpc.noaa.gov/json/boulder_k_index_1m.json)
product has `time_tag` and `k_index`. Boulder is a regional measurement and remains distinct
from planetary Kp.

The [OVATION aurora JSON](https://services.swpc.noaa.gov/json/ovation_aurora_latest.json)
has observation and forecast times, a stated `[Longitude, Latitude, Aurora]` format, and a
`MultiPoint` coordinate grid. The observed response held 65,160 points and about 920 KB.
The fixture uses a tiny grid with the same fields. The parser stores no grid. It samples only
configured LOCAL or REGIONAL coordinate windows, records the peak model value and sample count,
and labels the result as model output rather than observed visibility. No local tag is possible
without a configured location and an enabled ORBITAL parent policy.

All four registry candidates remain disabled. None is in the live HTTP allowlist. The OVATION
response also exceeds the current default fetch size cap; a future live decision must set and
verify a bounded cap, cadence, freshness, and attribution before enabling it.
