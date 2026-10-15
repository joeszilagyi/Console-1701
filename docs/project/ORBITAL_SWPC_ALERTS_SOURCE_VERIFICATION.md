# ORBITAL SWPC Alerts JSON Source Verification

Checked 2026-10-15 against NOAA SWPC's public [alerts JSON product](https://services.swpc.noaa.gov/products/alerts.json) and [product directory](https://services.swpc.noaa.gov/products/).

The observed JSON is an array. Each product has `product_id`, `issue_datetime`, and `message`.
The message is a NOAA text product with a message code, serial number, issue time, headline,
optional validity bounds, optional G/R/S scale, and source-provided potential-impact lines.
Observed samples included K-index warnings and alerts, geomagnetic watches and cancellations,
and an X-ray summary. The feed supplies no product-specific article URL; normalized items link
to the official feed with identity parameters and retain the exact feed URL separately.

The fixture contains a warning, a cancelled watch, and a malformed row. The parser skips
incomplete rows and stores bounded parsed facts, not the full message. `cancelled` is explicit so
later ranking cannot treat a cancelled watch as an active warning. A malformed top-level payload
reports parser failure. The local scan and facet tests make no HTTP request.

The registry candidate remains disabled. The exact endpoint is **not** in the live HTTP
allowlist. Before live admission, check refresh cadence, response size and conditional request
behavior, date freshness, cancellation ranking, and source-health handling under an explicit
opt-in scan.
