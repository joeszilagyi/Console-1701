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

NOAA's [Space Weather Scales table](https://www.spaceweather.gov/noaa-scales-explanation)
maps planetary Kp 5, 6, 7, 8 and 9 to geomagnetic G1, G2, G3, G4 and G5. The offline matcher
derives a level only from the observed three-hour planetary summary, and joins a same-level
SWPC warning/alert only when the Kp timestamp lies inside the warning's explicit valid window.
The provisional one-minute estimate and Boulder local K-index do not supply this match. A joined
pair is one SWPC source family, not independent corroboration or a local aurora claim.

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

On 2026-10-15, a read-only HEAD check of OVATION returned HTTP 200, `application/json`,
`ETag`, `Last-Modified`, and a 919 KB response. The exact endpoint is now in the live allowlist,
but registry and config defaults remain disabled. Live opt-in requires at least one validated
LOCAL/REGIONAL coordinate window with a modeled intensity floor of 50, verified status, and
explicit news/ORBITAL/source/HTTP enablement. The parser stores only a per-window peak and sample
count, never the full grid or a visibility claim. The scanner drops live model rows older than two
hours and forecasts outside one hour past to three hours ahead. The current response fits under
the default 1 MiB cap; if NOAA's grid grows, the scan fails with a bounded payload error until the
operator explicitly raises the configured cap (still subject to the transport's 4 MiB ceiling).
Mocked-transport tests cover the location gate, model-only provenance, and freshness. No live app
scan was run.
