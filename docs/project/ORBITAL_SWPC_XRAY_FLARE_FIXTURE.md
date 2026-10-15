# SWPC GOES X-ray flare fixture

Checked 2026-10-15 against the official [SWPC GOES X-ray product](https://www.swpc.noaa.gov/products/goes-x-ray-flux)
and its [public data service](https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json).
The registry's former `products/summary/x-ray-flux.json` URL returned HTTP 404. A bounded direct
GET of the seven-day flare event list returned HTTP 200, `application/json`, 21,256 bytes and 56
rows. Rows exposed begin, peak and end times, peak class, long-band flux and GOES satellite ID;
three rows had M-class peaks in this sample. The official product page describes the 1–8 Å
and 0.5–4 Å bands and links to SWPC's GOES JSON service.

The checked-in fixture keeps only three observed rows and their event metadata: two M-class
peaks and one C-class background row. `swpc_xray_flares_json` accepts at most 64 KiB/200 rows,
requires the exact ORBITAL source, stores only M1+ or X-class observations, rejects duplicate
satellite/start identities and invalid time/class/flux fields, and excludes C/B-class rows. It
stores peak class and flux as source measurements, never a claimed operational alert, radio
blackout, satellite effect, or Earth impact. Event identity query parameters are local dedupe
keys, not source-supported deep links. The rank uses a capped 12/20/30 severity contribution
for M1–M4, M5+, and X classes, with no public or operational impact boost from class alone.

The source stays disabled for HTTP. A separate live signoff would need a bounded request,
refresh/backoff choice, freshness handling, and source-health proof. The legacy source key
`swpc_xray_flux_summary` is retained for config compatibility, while its registry name/URL now
describe the verified flare event list.
