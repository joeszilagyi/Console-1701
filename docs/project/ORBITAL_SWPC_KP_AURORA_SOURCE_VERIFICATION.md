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

On 2026-10-15, read-only HEAD checks of the three K-index endpoints returned HTTP 200,
`application/json`, `ETag`, and `Last-Modified`. Response sizes were approximately 4.8 KB for
planetary summary, 28 KB for planetary one-minute, and 86 KB for Boulder one-minute. Their exact
URL/parser pairs are now in the live HTTP allowlist. Registry defaults remain disabled; local
opt-in requires verified status, explicit news/ORBITAL/source/HTTP enablement, and a K-index
floor of at least 5.0. The scanner keeps only the latest qualifying measurement and drops live
planetary summary records older than six hours, minute records older than one hour, or timestamps
more than ten minutes in the future. Mocked-transport tests cover those gates and persisted
provenance; no live app scan was run.

The OVATION candidate remains disabled and outside the live allowlist. Its response can approach
the current default fetch-size cap; live admission still needs an explicit bounded cap and
freshness check. The parser's configured coordinate window and model-only wording remain required.
